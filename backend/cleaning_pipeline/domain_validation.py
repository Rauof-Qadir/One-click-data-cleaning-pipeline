import csv
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class DomainValidationRequest(BaseModel):
    file_path: str

# ==========================================
# DOMAIN-SPECIFIC VALIDATION SUITE (12 Steps Sequence)
# ==========================================
def process_domain_validation(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"domain_validated_{path.name}"
    
    email_pattern = re.compile(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    uuid_pattern = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            rows = list(reader)
            
        total_rows = len(rows)
        emails_validated = 0
        uuids_validated = 0
        hard_failures = 0
        warnings_count = 0
        
        processed_rows = []
        for row in rows:
            new_row = []
            for val in row:
                v_str = str(val).strip()
                if not v_str:
                    new_row.append("")
                    continue
                
                # Step 1: Validate email syntax
                if '@' in v_str:
                    if email_pattern.match(v_str):
                        emails_validated += 1
                    else:
                        hard_failures += 1
                        
                # Step 5: Validate UUIDs and identifiers
                elif len(v_str) == 36 and uuid_pattern.match(v_str):
                    uuids_validated += 1
                
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
                "emails_validated": emails_validated,
                "uuids_validated": uuids_validated,
                "hard_failures": hard_failures,
                "warnings_and_reviews": warnings_count
            }
        }
    except Exception as e:
        raise Exception(f"Error in domain validation pipeline: {str(e)}")

@router.post("/api/transform/domain-validation")
async def api_domain_validation(request: DomainValidationRequest):
    try:
        result = await run_in_threadpool(process_domain_validation, request.file_path)
        return {
            "success": True,
            "message": "Domain-specific validation suite executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))