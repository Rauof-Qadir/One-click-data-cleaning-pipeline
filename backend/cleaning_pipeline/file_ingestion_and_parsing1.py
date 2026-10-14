import csv
import uuid
from pathlib import Path
import chardet
import gzip
import zipfile
import bz2
import shutil
import json

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = 8 * 1024 * 1024


# ==========================================
# PIPELINE STEP 0: Detect & Extract Compression
# ==========================================
def detect_and_extract_compression(path: Path):
    """
    Yeh function file ke 'Magic Bytes' check karega.
    Agar file compressed (ZIP, GZIP, BZIP2) hui, tou usay extract kar dega.
    """
    try:
        # Shuru ke 4 bytes (Magic Bytes) read karein
        with path.open("rb") as f:
            magic = f.read(4)

        is_compressed = False
        compression_type = "None"
        extracted_path = path

        # 1. GZIP check (\x1f\x8b)
        if magic.startswith(b'\x1f\x8b'):
            is_compressed = True
            compression_type = "GZIP"
            extracted_path = path.parent / f"extracted_{path.name}"
            with gzip.open(path, 'rb') as f_in, extracted_path.open('wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
                
        # 2. ZIP check (PK\x03\x04)
        elif magic.startswith(b'PK\x03\x04'):
            is_compressed = True
            compression_type = "ZIP"
            extracted_path = path.parent / f"extracted_{path.name}"
            with zipfile.ZipFile(path, 'r') as z:
                file_name = z.namelist()[0] # Pehli file nikal lein
                with z.open(file_name) as f_in, extracted_path.open('wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                    
        # 3. BZIP2 check (BZh)
        elif magic.startswith(b'BZh'):
            is_compressed = True
            compression_type = "BZIP2"
            extracted_path = path.parent / f"extracted_{path.name}"
            with bz2.open(path, 'rb') as f_in, extracted_path.open('wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        return {
            "is_compressed": is_compressed,
            "compression_type": compression_type,
            "working_path": extracted_path # Ab pipeline is path par chalegi
        }
    except Exception as e:
        return {
            "is_compressed": False,
            "compression_type": "Error/Unknown",
            "working_path": path # Error ki soorat mein original path hi de dein
        }
    
# ==========================================
# PIPELINE STEP 1: Quick CSV Validation
# ==========================================
def validate_csv(path: Path):
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            reader = csv.reader(file)
            try:
                header = next(reader)
            except StopIteration:
                return False, "The CSV file is empty."

            if not header or not any(cell.strip() for cell in header):
                return False, "The file contains only blank spaces or empty columns."

            return True, {
                "columns": len(header),
                "column_names": header,
                "file_path": path
            }
    except Exception as exc:
        return False, f"Cannot read file: {exc}"
    
# ==========================================
# PIPELINE STEP 2: Detect Encoding
# ==========================================
def detect_file_encoding(path: Path) -> str:
    with path.open("rb") as f:
        raw_data = f.read(10000)
    
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    
    return encoding if encoding else "utf-8-sig"


# ==========================================
# PIPELINE STEP 3: Detect Delimiter
# ==========================================
def detect_delimiter(path: Path, encoding: str) -> str:
    """Yeh function file ka text read kar ke delimiter guess karega."""
    try:
        # Pichle step ki encoding use kar ke file kholi
        with path.open("r", encoding=encoding, newline="") as file:
            # Sirf shuru ka thora sa data (4096 bytes) read karein guess karne ke liye
            sample = file.read(4096)
            
            # Python ka apna Sniffer in 4 delimiters mein se guess karega
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=[',', ';', '\t', '|'])
            
            return dialect.delimiter
    except Exception:
        # Agar file itni choti ya ajeeb ho ke sniffer guess na kar paye, tou default comma return karein
        return ","


# ==========================================
# PIPELINE STEP 4: Detect Quoting, Escaping & Line Breaks
# ==========================================
def detect_quoting_and_newlines(path: Path, encoding: str, delimiter: str):
    """
    Yeh function detect karega ke:
    1. Text ko kis character se quote kiya gaya hai (e.g., ")
    2. Escape character kya hai (e.g., \ )
    3. Kya kisi cell ke andar (embedded) line break mojood hai?
    """
    try:
        with path.open("r", encoding=encoding, newline="") as file:
            sample = file.read(4096)
            
            # Sniffer ko batayen ke humein delimiter pehle se pata hai
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample, delimiters=[delimiter])
            
            quotechar = dialect.quotechar
            escapechar = dialect.escapechar
            doublequote = dialect.doublequote
            
            # File pointer ko wapas shuru mein layen taake embedded newlines check kar sakein
            file.seek(0)
            
            # Detect kiye gaye rules (dialect) ke mutabiq CSV read karein
            reader = csv.reader(file, dialect=dialect)
            has_embedded_newlines = False
            
            # Shuru ki 100 rows check karte hain taake memory aur time bache
            row_count = 0
            for row in reader:
                if row_count > 100: 
                    break
                
                # Check karein ke kisi bhi column (cell) ke andar \n ya \r mojood hai ya nahi
                if any('\n' in cell or '\r' in cell for cell in row):
                    has_embedded_newlines = True
                    break
                    
                row_count += 1
                
            return {
                "quotechar": quotechar if quotechar else "None",
                "escapechar": escapechar if escapechar else "None",
                "doublequote": doublequote,
                "has_embedded_newlines": has_embedded_newlines
            }
            
    except Exception:
        # Agar detect na ho sake tou default CSV rules return karein
        return {
            "quotechar": '"',
            "escapechar": "None",
            "doublequote": True,
            "has_embedded_newlines": False
        }



# ==========================================
# PIPELINE STEP 5: Handle & Clean Headers
# ==========================================
def analyze_and_clean_headers(path: Path, encoding: str, delimiter: str, quotechar: str):
    """
    Yeh function pehli row (header) ko parhega aur:
    1. Khali (missing) headers ko naam dega (e.g., Unnamed_Column_1)
    2. Duplicate headers ko unique banayega (e.g., Name_1, Name_2)
    """
    try:
        # Puraane steps ki settings use karte hue file open karein
        q_char = quotechar if quotechar != "None" else '"'
        
        with path.open("r", encoding=encoding, newline="") as file:
            reader = csv.reader(file, delimiter=delimiter, quotechar=q_char)
            
            try:
                original_headers = next(reader)
            except StopIteration:
                return {"error": "File is empty"}

            cleaned_headers = []
            seen_headers = {}
            duplicates_found = False
            missing_found = False

            for index, col in enumerate(original_headers):
                # 1. Spaces khatam karein aur missing handle karein
                col_name = col.strip() if col else ""
                
                if not col_name:
                    missing_found = True
                    col_name = f"Unnamed_Column_{index + 1}"
                
                # 2. Duplicate handle karein
                if col_name in seen_headers:
                    duplicates_found = True
                    seen_headers[col_name] += 1
                    col_name = f"{col_name}_{seen_headers[col_name]}"
                else:
                    seen_headers[col_name] = 0
                    
                cleaned_headers.append(col_name)

            return {
                "original_headers": original_headers,
                "cleaned_headers": cleaned_headers,
                "duplicates_found": duplicates_found,
                "missing_found": missing_found,
                "is_modified": duplicates_found or missing_found
            }
            
    except Exception as e:
        return {"error": str(e)}



# ==========================================
# PIPELINE STEP 6: Detect Malformed Rows
# ==========================================
def detect_malformed_rows(path: Path, encoding: str, delimiter: str, quotechar: str, expected_columns: int):
    """
    Yeh function poori file scan karega. Agar kisi row mein columns ki tadad 
    header ke columns (expected_columns) se kam ya zyada hui, tou usay record karega.
    """
    malformed_rows = []
    total_rows = 0
    q_char = quotechar if quotechar != "None" else '"'

    try:
        with path.open("r", encoding=encoding, newline="") as file:
            reader = csv.reader(file, delimiter=delimiter, quotechar=q_char)
            
            # Header ko skip kar dein
            next(reader, None)
            
            for row_num, row in enumerate(reader, start=2): # Row 2 se data shuru hota hai
                total_rows += 1
                
                # Agar row ke columns header ke columns se match na karein
                if len(row) != expected_columns:
                    # Sirf pehli 50 kharab rows ki detail save karein taake memory full na ho
                    if len(malformed_rows) < 50:
                        malformed_rows.append({
                            "line_number": row_num,
                            "columns_found": len(row)
                        })

            return {
                "total_data_rows": total_rows,
                "malformed_count": len(malformed_rows), # Kitni kharab lines hain
                "malformed_details": malformed_rows,    # Unki details
                "is_clean": len(malformed_rows) == 0    # Kya data bilkul theek hai?
            }
            
    except Exception as e:
        return {"error": str(e)}



# ==========================================
# PIPELINE STEP 8: Detect BOM & Line Endings
# ==========================================
def detect_bom_and_line_endings(path: Path):
    """
    Yeh function file ke shuru ke bytes parh kar BOM detect karega, 
    aur Python ke 'universal newlines' ko use kar ke line endings check karega.
    """
    bom_info = "None"
    has_bom = False

    try:
        # 1. Check BOM (Binary mode mein pehle 4 bytes read karein)
        with path.open("rb") as f:
            raw_start = f.read(4)

        if raw_start.startswith(b'\xef\xbb\xbf'):
            has_bom = True
            bom_info = "UTF-8 BOM"
        elif raw_start.startswith(b'\xff\xfe'):
            has_bom = True
            bom_info = "UTF-16 LE BOM"
        elif raw_start.startswith(b'\xfe\xff'):
            has_bom = True
            bom_info = "UTF-16 BE BOM"

        # 2. Check Line Endings (Text mode mein)
        line_endings_found = []
        with path.open("r", encoding="utf-8", errors="ignore") as f:
            f.read(8192) # Thora sa data read karein taake Python newlines guess kar sake
            nl = f.newlines
            
            # Agar file mein koi newline nahi mili
            if nl is None:
                nl = ()
            # Agar ek hi kism ki newline mili tou usay tuple bana dein
            elif isinstance(nl, str):
                nl = (nl,)

            if '\r\n' in nl:
                line_endings_found.append("CRLF (Windows)")
            if '\n' in nl:
                line_endings_found.append("LF (Unix)")
            if '\r' in nl:
                line_endings_found.append("CR (Mac Classic)")

        return {
            "has_bom": has_bom,
            "bom_type": bom_info,
            "line_endings": " + ".join(line_endings_found) if line_endings_found else "Single Line",
            "mixed_line_endings": len(line_endings_found) > 1
        }
        
    except Exception as e:
        return {
            "has_bom": False,
            "bom_type": "None",
            "line_endings": "Unknown",
            "mixed_line_endings": False
        }




# ==========================================
# PIPELINE STEP 9: Standardize & Clean Data
# ==========================================
def standardize_csv_file(path: Path, encoding: str, delimiter: str, quotechar: str, cleaned_headers: list):
    """
    Yeh function original file ko parh kar ek nayi standard file banayega:
    - Embedded newlines (\n, \r) ko space se replace karega.
    - Quoted delimiters ko safely handle karega.
    - File ko hamesha UTF-8 aur Comma (,) format mein save karega.
    """
    cleaned_path = path.parent / f"standardized_{path.name}"
    q_char = quotechar if quotechar != "None" else '"'
    
    try:
        # Original file ko detected settings ke sath open karein
        with path.open("r", encoding=encoding, newline="") as infile, \
             cleaned_path.open("w", encoding="utf-8", newline="") as outfile:
             
            reader = csv.reader(infile, delimiter=delimiter, quotechar=q_char)
            # Nayi file hamesha standard CSV format (comma separated) mein hogi
            writer = csv.writer(outfile, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)
            
            # Original header skip karein
            next(reader, None)
            
            # Step 5 waley Cleaned Headers sab se pehle likhein
            writer.writerow(cleaned_headers)
            
            for row in reader:
                # Har cell (column) ke andar se embedded newlines ko space se replace kar dein
                clean_row = [cell.replace("\r\n", " ").replace("\n", " ").replace("\r", " ").strip() for cell in row]
                writer.writerow(clean_row)
                
        return {
            "standardized_file_path": str(cleaned_path),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e)}

    

# ==========================================
# PIPELINE STEP 10: Record Parsing Settings
# ==========================================
def save_metadata_and_preserve(original_path: Path, metadata: dict):
    """
    Yeh function original file ko preserve karta hai aur 
    tamam detect ki gayi settings ko ek JSON file mein save kar deta hai.
    """
    try:
        # JSON file ka naam original file ke naam par hi hoga bas extension .json hogi
        metadata_path = original_path.with_suffix('.json')
        
        # Dictionary ko JSON format mein save karein
        with metadata_path.open("w", encoding="utf-8") as json_file:
            json.dump(metadata, json_file, indent=4)
            
        return {
            "metadata_saved": True,
            "metadata_file": metadata_path.name
        }
    except Exception as e:
        return {
            "metadata_saved": False,
            "error": str(e)
        }





    
# ==========================================
# MAIN API ROUTE (PIPELINE CONTROLLER)
# ==========================================
@router.post("/api/upload")
async def upload_csv(file: UploadFile = File(...)):
    filename = file.filename or ""

    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only .csv files are accepted.",
        )

    saved_path = UPLOAD_DIR / f"{uuid.uuid4().hex}.csv"

    try:
        with saved_path.open("wb") as destination:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                destination.write(chunk)

        # ----------------------------------------------------
        # PIPELINE EXECUTION START
        # ----------------------------------------------------
        

         # 🔴 STEP 0: Detect Compression (NAYA STEP)
        compression_details = await run_in_threadpool(detect_and_extract_compression, saved_path)
        working_path = compression_details["working_path"] # Extracted (ya original) file ka path

        if working_path.stat().st_size == 0:
            working_path.unlink(missing_ok=True)
            if working_path != saved_path:
                saved_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail="The uploaded file is empty (0 bytes).")



        # STEP 1: Validate CSV
        is_valid, csv_result = await run_in_threadpool(validate_csv, working_path)
        
        if not is_valid:
            working_path.unlink(missing_ok=True)
            if working_path != saved_path:
                saved_path.unlink(missing_ok=True)
            raise HTTPException(status_code=400, detail=csv_result)

        # STEP 2: Detect Encoding (Step 1 ka path use kiya)
        detected_encoding = await run_in_threadpool(detect_file_encoding, csv_result["file_path"])
        
        # STEP 3: Detect Delimiter (Step 1 ka path aur Step 2 ki encoding use ki)
        detected_delimiter = await run_in_threadpool(
            detect_delimiter, 
            csv_result["file_path"], 
            detected_encoding
        )
        
        # STEP 4: Detect Quoting, Escaping & Line Breaks (Step 1, 2, aur 3 ka path use kiya)
        
        quote_details = await run_in_threadpool(
            detect_quoting_and_newlines,
            csv_result["file_path"],
            detected_encoding,
            detected_delimiter
        )

        # STEP 5: Analyze and Clean Headers (NAYA STEP)
        header_details = await run_in_threadpool(
            analyze_and_clean_headers,
            csv_result["file_path"],
            detected_encoding,
            detected_delimiter,
            quote_details["quotechar"]
        )

        # STEP 6: Detect Malformed Rows (NAYA STEP)
        row_details = await run_in_threadpool(
            detect_malformed_rows,
            csv_result["file_path"],
            detected_encoding,
            detected_delimiter,
            quote_details["quotechar"],
            len(header_details.get("cleaned_headers", [])) # Expected columns humein clean headers se milenge
        )


        # 🔴 STEP 7: Header-Only Check (Data Readiness)
        total_rows = row_details.get("total_data_rows", 0)
        is_header_only = (total_rows == 0)

        # 🔴 STEP 8: Detect BOM and Line Endings (NAYA STEP)
        system_details = await run_in_threadpool(detect_bom_and_line_endings, csv_result["file_path"])



        # 🔴 STEP 9: Handle Quotes & Newlines (Standardize File)
        # Yeh step tabhi chalega jab data mojood ho (is_header_only False ho)
        standardized_file = None
        if not is_header_only:
            standardization_result = await run_in_threadpool(
                standardize_csv_file,
                csv_result["file_path"],
                detected_encoding,
                detected_delimiter,
                quote_details["quotechar"],
                header_details.get("cleaned_headers", [])
            )
            if standardization_result.get("status") == "success":
                standardized_file = standardization_result["standardized_file_path"]


            # 🔴 STEP 10: Preserve File & Record Metadata (NAYA STEP)
        pipeline_metadata = {
            "original_filename": Path(filename).name,
            "saved_internal_name": saved_path.name,
            "size_bytes": saved_path.stat().st_size,
            "compression": {
                "was_compressed": compression_details["is_compressed"],
                "type": compression_details["compression_type"]
            },
            "parsing_settings": {
                "encoding": detected_encoding,
                "delimiter": detected_delimiter,
                "quotechar": quote_details["quotechar"],
                "escapechar": quote_details["escapechar"],
                "has_bom": system_details["has_bom"],
                "bom_type": system_details["bom_type"],
                "line_endings": system_details["line_endings"]
            },
            "data_quality": {
                "total_rows": total_rows,
                "total_columns": len(header_details.get("cleaned_headers", [])),
                "is_header_only": is_header_only,
                "has_embedded_newlines": quote_details["has_embedded_newlines"],
                "mixed_line_endings": system_details["mixed_line_endings"],
                "malformed_rows_count": row_details.get("malformed_count", 0),
                "headers_modified": header_details.get("is_modified", False)
            },
            "cleaned_headers": header_details.get("cleaned_headers", []),
            "standardized_file_generated": standardized_file is not None
        }

        # Metadata JSON file save karein
        meta_result = await run_in_threadpool(save_metadata_and_preserve, saved_path, pipeline_metadata)

        # ----------------------------------------------------
        # PIPELINE EXECUTION END
        # ----------------------------------------------------

        return {
            "success": True,
            "message": "CSV validated successfully!",
            "filename": Path(filename).name,
            "size_bytes": saved_path.stat().st_size,
            "rows": row_details.get("total_data_rows", 0),
            "columns": len(header_details.get("cleaned_headers", [])),
            "column_names": csv_result["column_names"],
            "encoding": detected_encoding,        # Output from Step 2
            "delimiter": detected_delimiter,      # Output from Step 3
            "quotechar": quote_details["quotechar"],
            "escapechar": quote_details["escapechar"],
            "has_embedded_newlines": quote_details["has_embedded_newlines"],
            # Step 5 ka result output mein bhej dein
            "cleaned_headers": header_details.get("cleaned_headers", []),
            "headers_modified": header_details.get("is_modified", False),
            "duplicates_fixed": header_details.get("duplicates_found", False),
            "missing_fixed": header_details.get("missing_found", False),

            # Step 6 ka Data frontend ke liye
            "malformed_count": row_details.get("malformed_count", 0),
            "is_clean_data": row_details.get("is_clean", True),
            "is_header_only": is_header_only,


            # Step 8 ka data
            "has_bom": system_details["has_bom"],
            "bom_type": system_details["bom_type"],
            "line_endings": system_details["line_endings"],
            "mixed_line_endings": system_details["mixed_line_endings"],

            "is_standardized": standardized_file is not None,

            "standardized_file_path": standardized_file if standardized_file else "",

            # Step 0 ka data frontend ko bhejein
            "is_compressed": compression_details["is_compressed"],
            "compression_type": compression_details["compression_type"],


            # Metadata step result
            "metadata_saved": meta_result.get("metadata_saved", False),
            "metadata_filename": meta_result.get("metadata_file", "")
            
        }

    except HTTPException:
        raise
    except OSError as exc:
        saved_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Could not save the file. Check available disk space.",
        ) from exc
    finally:
        await file.close()