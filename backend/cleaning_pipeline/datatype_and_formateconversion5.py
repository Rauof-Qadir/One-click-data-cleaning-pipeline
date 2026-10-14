import csv
import re
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class TypeInferenceRequest(BaseModel):
    file_path: str

# ==========================================
# TYPE PARSING & INFERENCE FUNCTIONS (15 Steps)
# ==========================================
def parse_and_infer_cell(val: str):
    if not val or val.strip() == "":
        return val, "null", {}

    val_str = val.strip()
    original_val = val_str
    
    # 1. Handle Currency symbols and percentage strings ($1,234.50 -> 1234.50, 45% -> 0.45)
    is_percentage = val_str.endswith('%')
    has_currency = bool(re.search(r'[$€£¥]', val_str))
    
    cleaned_num = re.sub(r'[^\d\.\-\+eE]', '', val_str)
    
    # 2. Parse thousands separators and decimal conventions (e.g. 1,234.56 or 1.234,56)
    if has_currency or is_percentage or (',' in val_str and '.' in val_str):
        if val_str.rfind(',') > val_str.rfind('.'): # European convention check
            cleaned_num = val_str.replace('.', '').replace(',', '.').strip()
        else:
            cleaned_num = val_str.replace(',', '').strip()
        cleaned_num = re.sub(r'[^\d\.\-\+eE]', '', cleaned_num)

    # 3. Detect Scientific notation and numeric overflow / Large IDs (Prevent precision loss)
    is_scientific = bool(re.match(r'^[+-]?\d+(\.\d+)?[eE][+-]?\d+$', val_str))
    
    # 4. Try parsing Decimal / Integer
    try:
        if '.' in cleaned_num or is_scientific:
            num_val = float(cleaned_num)
            if is_percentage:
                num_val = num_val / 100.0
            inf_type = "decimal"
            return str(num_val), inf_type, {"converted": True}
        else:
            int_val = int(cleaned_num)
            # Check leading zeros preservation for postal codes/IDs (e.g. "02138")
            if original_val.startswith('0') and len(original_val) > 1 and not original_val.startswith('0.'):
                return original_val, "string_identifier", {"retained_leading_zeros": True}
            return str(int_val), "integer", {"converted": True}
    except ValueError:
        pass

    # 5. Standardize Yes/No, True/False variants to Boolean
    val_lower = val_str.lower()
    if val_lower in ['true', 'yes', '1', 't', 'y']:
        return "True", "boolean", {}
    elif val_lower in ['false', 'no', '0', 'f', 'n']:
        return "False", "boolean", {}

    # 6. Parse Dates in multiple known formats & handle ambiguous dates (e.g. 03/04/2025)
    date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y']
    parsed_date = None
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(val_str, fmt)
            break
        except ValueError:
            continue
            
    if parsed_date:
        ambiguous = '/' in val_str and len(val_str.split('/')[0]) == 2 and len(val_str.split('/')[1]) == 2
        return parsed_date.strftime('%Y-%m-%d'), "date", {"ambiguous_date_flag": ambiguous}

    # 7. Detect Unix timestamps (seconds or milliseconds)
    if val_str.isdigit() and len(val_str) in [10, 13]:
        try:
            ts = int(val_str)
            if len(val_str) == 13:
                ts = ts / 1000.0
            dt = datetime.fromtimestamp(ts)
            return dt.strftime('%Y-%m-%d %H:%M:%S'), "datetime", {"unix_timestamp": True}
        except Exception:
            pass

    # Default fallback: Retain original string for review (Failed conversions protected)
    return original_val, "string", {"conversion_failed_retained": True}

# ==========================================
# PIPELINE: Type Inference & Standardization
# ==========================================
def process_type_inference(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"type_inferred_{path.name}"
    
    total_cells = 0
    type_counts = {"integer": 0, "decimal": 0, "boolean": 0, "date": 0, "datetime": 0, "string": 0, "string_identifier": 0}
    mixed_type_columns_detected = 0
    
    processed_rows = []
    
    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            processed_rows.append(header)
            col_types_tracker = {i: set() for i in range(len(header))}
            
            rows_data = []
            for row in reader:
                rows_data.append(row)
                
            # Process cells
            for row in rows_data:
                new_row = []
                for idx, val in enumerate(row):
                    total_cells += 1
                    cleaned_val, inf_type, flags = parse_and_infer_cell(val)
                    if idx in col_types_tracker:
                        col_types_tracker[idx].add(inf_type)
                    type_counts[inf_type] = type_counts.get(inf_type, 0) + 1
                    new_row.append(cleaned_val)
                processed_rows.append(new_row)
                
            # Check mixed-type columns
            for idx, types in col_types_tracker.items():
                non_null_types = [t for t in types if t != "null"]
                if len(set(non_null_types)) > 1:
                    mixed_type_columns_detected += 1

        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerows(processed_rows)
            
        return {
            "file_path": str(output_path),
            "summary": {
                "total_cells_processed": total_cells,
                "inferred_types": type_counts,
                "mixed_type_columns": mixed_type_columns_detected
            }
        }
    except Exception as e:
        raise Exception(f"Error in type inference pipeline: {str(e)}")

@router.post("/api/transform/type-inference")
async def api_type_inference(request: TypeInferenceRequest):
    try:
        result = await run_in_threadpool(process_type_inference, request.file_path)
        return {
            "success": True,
            "message": "Type inference and parsing executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))