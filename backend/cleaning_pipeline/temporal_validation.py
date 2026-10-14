import csv
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class TemporalValidationRequest(BaseModel):
    file_path: str

# ==========================================
# TEMPORAL VALIDATION & DATE/TIME SUITE (12 Steps Sequence)
# ==========================================
def process_temporal_validation(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"temporal_validated_{path.name}"
    
    date_formats = ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d', '%d-%m-%Y', '%m-%d-%Y', '%Y-%m-%d %H:%M:%S']

    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            rows = list(reader)
            
        total_rows = len(rows)
        dates_standardized = 0
        invalid_dates_detected = 0
        ambiguous_orders_count = 0
        out_of_range_count = 0
        
        processed_rows = []
        for row in rows:
            new_row = []
            for val in row:
                v_str = str(val).strip()
                if not v_str:
                    new_row.append("")
                    continue
                
                parsed_dt = None
                is_ambiguous = False
                
                # Check ambiguous day/month order (e.g. 03/04/2025)
                if '/' in v_str and len(v_str.split('/')) == 3:
                    parts = v_str.split('/')
                    if len(parts[0]) == 2 and len(parts[1]) == 2:
                        is_ambiguous = True
                        ambiguous_orders_count += 1

                for fmt in date_formats:
                    try:
                        parsed_dt = datetime.strptime(v_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if parsed_dt:
                    # Check future or past bounds outside allowed business ranges (e.g. year < 1900 or > 2100)
                    if parsed_dt.year < 1900 or parsed_dt.year > 2100:
                        out_of_range_count += 1
                        new_row.append(v_str) # Retain for review
                    else:
                        dates_standardized += 1
                        new_row.append(parsed_dt.strftime('%Y-%m-%d'))
                else:
                    if any(char.isdigit() for char in v_str) and ('/' in v_str or '-' in v_str):
                        invalid_dates_detected += 1
                    new_row.append(v_str)
            processed_rows.append(new_row)

        # Write output file
        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(processed_rows)
            
        return {
            "file_path": str(output_path),
            "summary": {
                "total_rows_scanned": total_rows,
                "dates_standardized": dates_standardized,
                "invalid_dates_detected": invalid_dates_detected,
                "ambiguous_orders_detected": ambiguous_orders_count,
                "out_of_range_dates": out_of_range_count
            }
        }
    except Exception as e:
        raise Exception(f"Error in temporal validation pipeline: {str(e)}")

@router.post("/api/transform/temporal-validation")
async def api_temporal_validation(request: TemporalValidationRequest):
    try:
        result = await run_in_threadpool(process_temporal_validation, request.file_path)
        return {
            "success": True,
            "message": "Temporal validation and date/time suite executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))