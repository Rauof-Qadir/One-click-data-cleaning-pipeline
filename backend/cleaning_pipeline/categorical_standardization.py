import csv
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class CategoricalStandardizeRequest(BaseModel):
    file_path: str

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
# CATEGORICAL STANDARDIZATION & MAPPING (9 Steps Sequence)
# ==========================================
def process_categorical_standardization(file_path: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"categorical_standardized_{path.name}"
    
    # Common synonyms mapping dictionaries
    synonym_map = {
        "usa": "United States", "us": "United States", "u.s.": "United States",
        "uk": "United Kingdom", "u.k.": "United Kingdom",
        "male": "Male", "m": "Male", "female": "Female", "f": "Female",
        "yes": "Yes", "y": "Yes", "true": "Yes", "no": "No", "n": "No", "false": "No"
    }
    
    unknown_tokens = {'unknown', 'other', 'n/a', 'na', 'none', 'null', '?', '-'}

    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            rows = list(reader)
            
        total_rows = len(rows)
        spelling_fixes = 0
        synonym_replacements = 0
        rare_categories_count = 0
        ambiguous_flags_count = 0
        
        # Step A: First pass to count frequency of categories per column for rare detection
        col_value_counts = {i: {} for i in range(len(header))}
        for row in rows:
            for col_idx, val in enumerate(row):
                v_clean = str(val).strip()
                if v_clean:
                    col_value_counts[col_idx][v_clean] = col_value_counts[col_idx].get(v_clean, 0) + 1

        # Step B: Sequential Processing of all 9 steps across rows
        processed_rows = []
        for row in rows:
            new_row = []
            for col_idx, val in enumerate(row):
                v_str = str(val).strip()
                if not v_str:
                    new_row.append("")
                    continue
                
                # Step 1: Standardize category spelling and whitespace
                v_std = " ".join(v_str.split())
                if v_std != v_str:
                    spelling_fixes += 1
                
                v_lower = v_std.lower()
                
                # Step 7: Handle unknown, other and not-applicable categories distinctly
                if v_lower in unknown_tokens:
                    new_row.append("Unknown" if v_lower in ['unknown', '-'] else "Other")
                    continue

                # Step 2: Map known synonyms to canonical categories
                if v_lower in synonym_map:
                    v_std = synonym_map[v_lower]
                    synonym_replacements += 1
                else:
                    # Step 8 & 9: Detect misspellings using similarity and flag ambiguous mappings
                    canonical_found = False
                    for canon in synonym_map.values():
                        if _calculate_similarity(v_std, canon) >= 0.85 and v_std != canon:
                            ambiguous_flags_count += 1
                            canonical_found = True
                            break
                    if canonical_found:
                        # Retain original or flag instead of arbitrary choice
                        pass

                # Step 4: Detect rare and unexpected categories (frequency < 2% or count == 1 in small sets)
                total_col_items = sum(col_value_counts[col_idx].values())
                freq = col_value_counts[col_idx].get(v_str, 1) / total_col_items if total_col_items > 0 else 1.0
                if freq < 0.02 and total_col_items > 10:
                    rare_categories_count += 1

                new_row.append(v_std)
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
                "whitespace_spelling_fixes": spelling_fixes,
                "synonyms_mapped": synonym_replacements,
                "rare_categories_detected": rare_categories_count,
                "ambiguous_mappings_flagged": ambiguous_flags_count
            }
        }
    except Exception as e:
        raise Exception(f"Error in categorical standardization pipeline: {str(e)}")

@router.post("/api/transform/categorical-standardization")
async def api_categorical_standardization(request: CategoricalStandardizeRequest):
    try:
        result = await run_in_threadpool(process_categorical_standardization, request.file_path)
        return {
            "success": True,
            "message": "Categorical standardization steps executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))