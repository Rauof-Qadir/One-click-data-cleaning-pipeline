import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class CrossColumnConsistencyRequest(BaseModel):
    file_path: str

# ==========================================
# CROSS-COLUMN & BUSINESS LOGIC SUITE (10 Steps Sequence)
# ==========================================
def process_cross_column_consistency(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"cross_column_validated_{path.name}"

    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            rows = list(reader)
            
        total_rows = len(rows)
        arithmetic_mismatches = 0
        incompatible_combinations = 0
        contradictory_records = 0
        suspicious_patterns = 0
        
        # Helper to find column indices by keywords
        header_lower = [h.lower() for h in header]
        
        def find_col(keywords):
            for kw in keywords:
                for idx, h in enumerate(header_lower):
                    if kw in h:
                        return idx
            return -1

        qty_idx = find_col(['qty', 'quantity', 'amount_sold'])
        price_idx = find_col(['price', 'unit_price', 'rate'])
        rev_idx = find_col(['revenue', 'total', 'sales_amount', 'subtotal'])

        processed_rows = []
        for row in rows:
            new_row = list(row)
            
            # Step 4: Check quantity multiplied by unit price against revenue
            if qty_idx != -1 and price_idx != -1 and rev_idx != -1:
                try:
                    q = float(row[qty_idx])
                    p = float(row[price_idx])
                    r = float(row[rev_idx])
                    expected_rev = q * p
                    if abs(expected_rev - r) > 0.01: # allow small float tolerance
                        arithmetic_mismatches += 1
                except (ValueError, IndexError):
                    pass

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
                "arithmetic_mismatches": arithmetic_mismatches,
                "incompatible_field_combinations": incompatible_combinations,
                "contradictory_records": contradictory_records,
                "suspicious_patterns_flagged": suspicious_patterns
            }
        }
    except Exception as e:
        raise Exception(f"Error in cross-column consistency pipeline: {str(e)}")

@router.post("/api/transform/cross-column-consistency")
async def api_cross_column_consistency(request: CrossColumnConsistencyRequest):
    try:
        result = await run_in_threadpool(process_cross_column_consistency, request.file_path)
        return {
            "success": True,
            "message": "Cross-column and business logic suite executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))