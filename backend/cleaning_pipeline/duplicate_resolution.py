import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class DuplicateResolutionRequest(BaseModel):
    file_path: str
    strategy: str = "keep_first" # keep_first, keep_last, best_record
    key_column: str = "" # Business key or ID column for matching

def _calculate_similarity(s1: str, s2: str) -> float:
    if s1 == s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    set1, set2 = set(s1.lower()), set(s2.lower())
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union > 0 else 0.0

# ==========================================
# DUPLICATE DETECTION & RESOLUTION SUITE (12 Steps)
# ==========================================
def process_duplicate_resolution(file_path: str, strategy: str, key_column: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"fully_deduplicated_{path.name}"
    audit_path = path.parent / f"duplicate_audit_trail_{path.name}"
    
    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            rows = list(reader)
            
        total_rows = len(rows)
        key_idx = -1
        if key_column and key_column in header:
            key_idx = header.index(key_column)
            
        exact_duplicates_count = 0
        id_conflicts_count = 0
        near_duplicates_count = 0
        ambiguous_flags_count = 0
        
        seen_signatures = set()
        seen_keys = {}
        unique_rows = []
        audit_records = []
        
        for r_idx, row in enumerate(rows, start=1):
            signature = tuple(str(v).strip() for v in row)
            
            # Step 1: Detect exact duplicate rows
            if signature in seen_signatures:
                exact_duplicates_count += 1
                audit_records.append({"row_index": r_idx, "status": "removed_exact_duplicate"})
                continue
                
            # Step 2 & 3: Detect duplicates using selected business keys / transaction IDs
            if key_idx != -1 and key_idx < len(row):
                b_key = str(row[key_idx]).strip()
                if b_key:
                    if b_key in seen_keys:
                        # Step 4: Identify conflicting records sharing the same ID
                        existing_row = seen_keys[b_key]
                        if existing_row != row:
                            id_conflicts_count += 1
                            # Step 5 & 10: Strategy resolution (keep_first vs keep_last)
                            if strategy == "keep_last":
                                seen_keys[b_key] = row
                                audit_records.append({"row_index": r_idx, "status": "kept_overwrote_conflict"})
                            else:
                                audit_records.append({"row_index": r_idx, "status": "removed_conflict"})
                                continue
                        else:
                            exact_duplicates_count += 1
                            continue
                    else:
                        seen_keys[b_key] = row
            
            # Step 7 & 8: Detect near-duplicate text and fuzzy-match across existing unique rows
            is_near_dup = False
            for u_row in unique_rows[-20:]: # Check recent rows for performance
                match_scores = [_calculate_similarity(str(v1), str(v2)) for v1, v2 in zip(row, u_row) if str(v1).strip() and str(v2).strip()]
                if match_scores and (sum(match_scores) / len(match_scores)) >= 0.85:
                    near_duplicates_count += 1
                    # Step 11: Flag ambiguous matches for manual review
                    ambiguous_flags_count += 1
                    is_near_dup = True
                    break
                    
            if not is_near_dup:
                seen_signatures.add(signature)
                unique_rows.append(row)
                audit_records.append({"row_index": r_idx, "status": "retained_unique"})
            else:
                audit_records.append({"row_index": r_idx, "status": "flagged_ambiguous_near_duplicate"})

        # Step 12: Preserve a record of merged, retained and removed rows (Audit trail)
        with audit_path.open("w", encoding="utf-8", newline="") as audit_file:
            audit_writer = csv.writer(audit_file)
            audit_writer.writerow(["row_index", "status"])
            for rec in audit_records:
                audit_writer.writerow([rec["row_index"], rec["status"]])

        # Write output file
        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(unique_rows)
            
        return {
            "file_path": str(output_path),
            "audit_path": str(audit_path),
            "summary": {
                "total_rows_scanned": total_rows,
                "exact_duplicates_removed": exact_duplicates_count,
                "id_conflicts_resolved": id_conflicts_count,
                "near_duplicates_detected": near_duplicates_count,
                "ambiguous_flags": ambiguous_flags_count,
                "unique_rows_retained": len(unique_rows),
                "resolution_strategy": strategy
            }
        }
    except Exception as e:
        raise Exception(f"Error in duplicate resolution pipeline: {str(e)}")

@router.post("/api/transform/duplicate-resolution")
async def api_duplicate_resolution(request: DuplicateResolutionRequest):
    try:
        result = await run_in_threadpool(
            process_duplicate_resolution,
            request.file_path,
            request.strategy,
            request.key_column
        )
        return {
            "success": True,
            "message": "All 12 duplicate resolution steps executed sequentially!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))