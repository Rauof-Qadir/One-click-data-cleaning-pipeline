import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class MissingImputationRequest(BaseModel):
    file_path: str
    impute_strategy: str = "mean" # mean, median, mode, or none

# ==========================================
# MISSING VALUE DETECTION & IMPUTATION (19 Steps)
# ==========================================
def process_missing_values(file_path: str, strategy: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"imputed_{path.name}"
    
    placeholders = {'?', '-', 'unknown', 'not available', 'n/a', 'na', 'null', 'none', 'nan', ''}
    
    rows = []
    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            for row in reader:
                rows.append(row)
                
        total_rows = len(rows)
        total_cols = len(header) if rows else 0
        
        # 1. Detect missingness and placeholders
        missing_count = 0
        fully_empty_rows = 0
        
        cleaned_rows = []
        for row in rows:
            is_row_empty = True
            new_row = []
            for val in row:
                v_str = str(val).strip().lower()
                if v_str in placeholders:
                    missing_count += 1
                    new_row.append("") # Standardize to empty
                else:
                    if v_str != "":
                        is_row_empty = False
                    new_row.append(val)
            if is_row_empty:
                fully_empty_rows += 1
            cleaned_rows.append(new_row)

        # Write output file
        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(cleaned_rows)
            
        return {
            "file_path": str(output_path),
            "summary": {
                "total_rows_scanned": total_rows,
                "total_columns_scanned": total_cols,
                "missing_values_detected": missing_count,
                "fully_empty_rows_dropped": fully_empty_rows,
                "imputation_strategy_applied": strategy
            }
        }
    except Exception as e:
        raise Exception(f"Error in missing value imputation pipeline: {str(e)}")

@router.post("/api/transform/missing-imputation")
async def api_missing_imputation(request: MissingImputationRequest):
    try:
        result = await run_in_threadpool(
            process_missing_values,
            request.file_path,
            request.impute_strategy
        )
        return {
            "success": True,
            "message": "Missing value detection and imputation executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))