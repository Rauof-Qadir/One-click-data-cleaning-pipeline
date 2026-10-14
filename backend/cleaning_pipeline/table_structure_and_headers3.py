import csv
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class TransformHeadersRequest(BaseModel):
    file_path: str
    normalization_style: str = "snake_case"

def normalize_header(header: str, style: str) -> str:
    cleaned = header.strip()
    cleaned = re.sub(r'[^\w\s]', '', cleaned)
    
    if style == "snake_case":
        cleaned = re.sub(r'\s+', '_', cleaned).lower()
        cleaned = cleaned.strip('_')
    elif style == "lowercase":
        cleaned = cleaned.lower()
    elif style == "uppercase":
        cleaned = cleaned.upper()
        
    return cleaned

# Simple string similarity / distance function for typo detection
def _calculate_similarity(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    # Jaccard / Character overlap similarity approximation
    set1, set2 = set(s1), set(s2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

# ==========================================
# PIPELINE: Header Processing + Typo / Near-Duplicate Detection
# ==========================================
def process_header_pipeline(file_path: str, normalization_style: str):
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"cleaned_headers_{path.name}"
    processed_columns = []
    flags_info = []
    mistaken_header_rows = []
    repeated_header_rows = []
    shifted_value_rows = []
    empty_rows_indices = []
    near_duplicate_pairs = [] # Typos / near-duplicates track karne ke liye
    
    auto_gen_patterns = re.compile(r'^(unnamed|col|column|index|level_\d+)\b', re.IGNORECASE)
    multi_value_delimiters = [',', ';', '|']
    column_sample_values = {}
    
    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"processed_columns": [], "flags": [], "file_path": str(path)}
                
            original_header_raw = [str(h).strip() for h in header]
            raw_processed = [normalize_header(h, normalization_style) for h in header]
            
            seen_counts = {}
            final_headers = []
            original_header_set = {h.strip().lower() for h in header if h.strip()}
            
            for idx, (orig_h, h) in enumerate(zip(header, raw_processed)):
                is_empty = (orig_h.strip() == "")
                is_unnamed = is_empty or h.startswith("unnamed")
                is_auto_generated = bool(auto_gen_patterns.match(h)) or h.isdigit()
                
                if is_empty:
                    h = "unnamed_column"
                    
                if h in seen_counts:
                    seen_counts[h] += 1
                    unique_h = f"{h}_{seen_counts[h]}"
                    final_headers.append(unique_h)
                else:
                    seen_counts[h] = 0
                    final_headers.append(h)
                    
                column_name = final_headers[-1]
                column_sample_values[column_name] = []
                flags_info.append({
                    "column": column_name,
                    "is_empty": is_empty,
                    "is_unnamed": is_unnamed,
                    "is_auto_generated": is_auto_generated,
                    "has_multiple_values": False,
                    "is_fully_empty_column": False,
                    "is_spreadsheet_index": False,
                    "is_near_duplicate": False # Initialize
                })
            
            processed_columns = final_headers
            
            # Step A: Check for near-duplicates among column names
            for i in range(len(processed_columns)):
                for j in range(i + 1, len(processed_columns)):
                    c1 = processed_columns[i]
                    c2 = processed_columns[j]
                    # Agar similarity high ho lekin exact match na ho (typo / near-duplicate)
                    sim = _calculate_similarity(c1, c2)
                    if 0.75 <= sim < 1.0:
                        near_duplicate_pairs.append((c1, c2))
                        flags_info[i]["is_near_duplicate"] = True
                        flags_info[j]["is_near_duplicate"] = True

            all_data_rows = []
            sample_rows = []
            
            row_idx = 1
            for row in reader:
                all_data_rows.append(row)
                if len(sample_rows) < 50:
                    sample_rows.append(row)
                
                if not any(str(cell).strip() for cell in row):
                    empty_rows_indices.append(row_idx)

                if row_idx <= 100:
                    for i, val in enumerate(row):
                        if i < len(column_sample_values):
                            c_name = processed_columns[i]
                            if val.strip():
                                column_sample_values[c_name].append(val.strip())
                                
                current_row_trimmed = [str(v).strip() for v in row]
                
                if current_row_trimmed == original_header_raw:
                    repeated_header_rows.append(row_idx)
                else:
                    non_empty_vals = [val.lower() for val in current_row_trimmed if val]
                    match_count = sum(1 for val in non_empty_vals if val in original_header_set)
                    if len(original_header_set) > 0 and (match_count / len(original_header_set) >= 0.7):
                        mistaken_header_rows.append(row_idx)

                row_idx += 1

            for col_idx, flag in enumerate(flags_info):
                c_name = flag["column"]
                vals = column_sample_values.get(c_name, [])
                
                col_total_non_empty = sum(1 for r in all_data_rows if col_idx < len(r) and str(r[col_idx]).strip())
                if col_total_non_empty == 0:
                    flag["is_fully_empty_column"] = True
                
                is_named_index = any(k in c_name.lower() for k in ["unnamed", "index", "row_id", "seq"])
                if is_named_index and vals:
                    is_sequential = True
                    try:
                        int_vals = [int(float(v)) for v in vals[:20]]
                        for seq_i, val_int in enumerate(int_vals):
                            if val_int != seq_i and val_int != seq_i + 1:
                                is_sequential = False
                                break
                    except ValueError:
                        is_sequential = False
                    
                    if is_sequential or is_named_index:
                        flag["is_spreadsheet_index"] = True

            column_expected_types = {}
            for col_idx in range(len(processed_columns)):
                col_vals = [r[col_idx].strip() for r in sample_rows if col_idx < len(r) and r[col_idx].strip()]
                if not col_vals:
                    column_expected_types[col_idx] = "unknown"
                    continue
                numeric_count = sum(1 for v in col_vals if _is_numeric(v))
                if (numeric_count / len(col_vals)) >= 0.8:
                    column_expected_types[col_idx] = "numeric"
                else:
                    column_expected_types[col_idx] = "text"

            for r_idx, row in enumerate(all_data_rows, start=1):
                type_mismatch_count = 0
                non_empty_count = 0
                for i, val in enumerate(row):
                    if i in column_expected_types and val.strip():
                        non_empty_count += 1
                        if column_expected_types[i] == "numeric" and not _is_numeric(val.strip()):
                            type_mismatch_count += 1
                if non_empty_count >= 3 and (type_mismatch_count / non_empty_count) >= 0.5:
                    if r_idx not in empty_rows_indices:
                        shifted_value_rows.append(r_idx)

        for flag in flags_info:
            c_name = flag["column"]
            vals = column_sample_values.get(c_name, [])
            if vals:
                delimiter_match_count = sum(1 for v in vals if any(d in v for d in multi_value_delimiters))
                if (delimiter_match_count / len(vals)) >= 0.3:
                    flag["has_multiple_values"] = True

        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(processed_columns)
            for row in all_data_rows:
                writer.writerow(row)
                
        return {
            "processed_columns": processed_columns,
            "column_flags": flags_info,
            "mistaken_header_rows": mistaken_header_rows,
            "repeated_header_rows": repeated_header_rows,
            "shifted_value_rows": shifted_value_rows,
            "empty_rows_indices": empty_rows_indices,
            "near_duplicate_pairs": near_duplicate_pairs,
            "file_path": str(output_path)
        }
    except Exception as e:
        raise Exception(f"Error processing headers: {str(e)}")

def _is_numeric(val: str) -> bool:
    try:
        float(val)
        return True
    except ValueError:
        return False

@router.post("/api/transform/clean-headers")
async def api_clean_headers(request: TransformHeadersRequest):
    try:
        result = await run_in_threadpool(
            process_header_pipeline, 
            request.file_path, 
            request.normalization_style
        )
        return {
            "success": True,
            "message": "Headers cleaned and near-duplicate typos flagged successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))