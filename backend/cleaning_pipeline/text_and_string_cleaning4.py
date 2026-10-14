import csv
import re
import unicodedata
import traceback
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class TextStandardizeRequest(BaseModel):
    file_path: str
    semantic_capitalization: bool = False

def clean_and_detect_cell_value(val: str):
    if not val:
        return "", {
            "has_mojibake": False,
            "has_leading_trailing_space": False,
            "has_mixed_scripts": False,
            "is_truncated": False
        }
        
    original_val = val
    
    # 1. Normalize tabs, newlines and non-breaking spaces
    val = val.replace('\u00a0', ' ')
    val = re.sub(r'[\r\n\t]+', ' ', val)
    
    # 2. Remove unwanted control and zero-width characters
    val = re.sub(r'[\u200b-\u200d\ufeff]', '', val)
    val = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', val)
    
    # 3. Normalize Unicode consistently (NFC)
    val = unicodedata.normalize('NFC', val)
    
    # 4. Detect mojibake and encoding corruption
    has_mojibake = bool(re.search(r'[ÃÂâ€ðŸ]', val))
    
    # 5. Normalize punctuation and typographic variants
    val = val.replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    val = val.replace('–', '-').replace('—', '-')
    
    # 6. Normalize common missing tokens
    missing_tokens_set = {'na', 'n/a', 'null', 'none', 'blank', 'nan', 'undefined', '?'}
    if val.strip().lower() in missing_tokens_set:
        val = ""
        
    # 7. Standardize yes/no and true/false variants
    val_lower = val.strip().lower()
    if val_lower in ['yes', 'y', 'true', '1', 't']:
        val = "True"
    elif val_lower in ['no', 'n', 'false', '0', 'f']:
        val = "False"
        
    # 8. Normalize repeated internal spaces where safe
    val = re.sub(r'\s+', ' ', val)
    
    # 9. Trim leading and trailing whitespace
    has_leading_trailing_space = val != original_val.strip()
    val = val.strip()
    
    # 10. Detect unexpected characters and mixed scripts
    has_mixed_scripts = bool(re.search(r'[A-Za-z]', val)) and bool(re.search(r'[\u0400-\u04FF]', val))
    
    # 11. Detect suspicious text truncation
    is_truncated = val.endswith('...') or val.endswith('…')
    
    flags = {
        "has_mojibake": has_mojibake,
        "has_leading_trailing_space": has_leading_trailing_space,
        "has_mixed_scripts": has_mixed_scripts,
        "is_truncated": is_truncated
    }
    
    return val, flags

def process_text_standardization(file_path: str, semantic_capitalization: bool):
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"text_standardized_{path.name}"
    
    total_cells_scanned = 0
    mojibake_count = 0
    whitespace_issues_count = 0
    truncated_count = 0
    mixed_script_count = 0
    
    processed_rows = []
    
    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            processed_rows.append(header)
            
            for row in reader:
                new_row = []
                for val in row:
                    total_cells_scanned += 1
                    cleaned_val, flags = clean_and_detect_cell_value(val)
                    
                    if flags.get("has_mojibake", False): mojibake_count += 1
                    if flags.get("has_leading_trailing_space", False): whitespace_issues_count += 1
                    if flags.get("is_truncated", False): truncated_count += 1
                    if flags.get("has_mixed_scripts", False): mixed_script_count += 1
                    
                    new_row.append(cleaned_val)
                processed_rows.append(new_row)
                
        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(processed_rows)
            
        return {
            "file_path": str(output_path),
            "summary": {
                "total_cells_scanned": total_cells_scanned,
                "mojibake_detected": mojibake_count,
                "whitespace_issues_fixed": whitespace_issues_count,
                "truncated_texts_detected": truncated_count,
                "mixed_scripts_detected": mixed_script_count
            }
        }
    except Exception as e:
        print("--- ERROR IN TEXT STANDARDIZATION ---")
        traceback.print_exc()
        raise e

@router.post("/api/transform/text-standardization")
async def api_text_standardization(request: TextStandardizeRequest):
    try:
        result = await run_in_threadpool(
            process_text_standardization,
            request.file_path,
            request.semantic_capitalization
        )
        return {
            "success": True,
            "message": "Text standardization pipeline executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))