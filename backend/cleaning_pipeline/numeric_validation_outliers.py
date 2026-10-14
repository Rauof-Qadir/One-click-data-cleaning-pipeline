import csv
import math
import statistics
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class NumericValidationRequest(BaseModel):
    file_path: str
    strategy: str = "flag" # flag, cap, winsorize, exclude

# ==========================================
# NUMERIC VALIDATION & OUTLIER DETECTION (14 Steps)
# ==========================================
def process_numeric_validation(file_path: str, strategy: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"numeric_validated_{path.name}"
    
    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            rows = list(reader)
            
        total_rows = len(rows)
        total_cells_checked = 0
        invalid_numeric_strings = 0
        infinity_count = 0
        outliers_detected = 0
        
        # Step A: Collect numeric columns data for statistical outlier detection (IQR)
        col_numeric_values = {i: [] for i in range(len(header))}
        parsed_rows = []
        
        for row in rows:
            parsed_row = []
            for col_idx, val in enumerate(row):
                total_cells_checked += 1
                v_str = str(val).strip()
                
                # Check infinity
                if v_str.lower() in ['inf', '+inf', '-inf', 'infinity', '-infinity']:
                    infinity_count += 1
                    parsed_row.append("")
                    continue
                    
                try:
                    num_val = float(v_str)
                    if math.isnan(num_val) or math.isinf(num_val):
                        infinity_count += 1
                        parsed_row.append("")
                    else:
                        parsed_row.append(num_val)
                        col_numeric_values[col_idx].append(num_val)
                except ValueError:
                    if v_str != "":
                        invalid_numeric_strings += 1
                    parsed_row.append(v_str)
            parsed_rows.append(parsed_row)
            
        # Step B: Calculate IQR bounds for each numeric column to detect outliers
        col_bounds = {}
        for col_idx, vals in col_numeric_values.items():
            if len(vals) >= 4:
                sorted_vals = sorted(vals)
                q1_idx = int(len(sorted_vals) * 0.25)
                q3_idx = int(len(sorted_vals) * 0.75)
                q1 = sorted_vals[q1_idx]
                q3 = sorted_vals[q3_idx]
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                col_bounds[col_idx] = (lower_bound, upper_bound)
            else:
                col_bounds[col_idx] = (None, None)

        # Step C: Process rows based on strategy (flag, cap, winsorize, exclude)
        final_output_rows = []
        for parsed_row in parsed_rows:
            cleaned_row = []
            for col_idx, val in enumerate(parsed_row):
                if isinstance(val, (int, float)):
                    lb, ub = col_bounds.get(col_idx, (None, None))
                    if lb is not None and ub is not None:
                        if val < lb or val > ub:
                            outliers_detected += 1
                            if strategy == "cap":
                                val = ub if val > ub else lb
                            elif strategy == "exclude":
                                val = ""
                cleaned_row.append(str(val) if val is not None else "")
            final_output_rows.append(cleaned_row)

        # Write output file
        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(final_output_rows)
            
        return {
            "file_path": str(output_path),
            "summary": {
                "total_rows_scanned": total_rows,
                "invalid_numeric_strings": invalid_numeric_strings,
                "infinity_detected": infinity_count,
                "outliers_detected": outliers_detected,
                "validation_strategy": strategy
            }
        }
    except Exception as e:
        raise Exception(f"Error in numeric validation pipeline: {str(e)}")

@router.post("/api/transform/numeric-validation")
async def api_numeric_validation(request: NumericValidationRequest):
    try:
        result = await run_in_threadpool(
            process_numeric_validation,
            request.file_path,
            request.strategy
        )
        return {
            "success": True,
            "message": "Numeric validation and outlier detection executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))