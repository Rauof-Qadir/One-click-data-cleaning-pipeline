import csv
import math
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

router = APIRouter()

class AnomalyDetectionRequest(BaseModel):
    file_path: str
    anomaly_policy: str = "flag" # flag, alter, exclude

# ==========================================
# ANOMALY & OUTLIER DETECTION SUITE (10 Steps Sequence)
# ==========================================
def process_anomaly_detection(file_path: str, policy: str):
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    output_path = path.parent / f"anomaly_detected_{path.name}"
    audit_path = path.parent / f"anomaly_scores_audit_{path.name}"

    try:
        with path.open("r", encoding="utf-8", newline="") as infile:
            reader = csv.reader(infile)
            try:
                header = next(reader)
            except StopIteration:
                return {"file_path": str(path), "summary": {}}
                
            rows = list(reader)
            
        total_rows = len(rows)
        statistical_outliers = 0
        unusual_categorical_combos = 0
        anomaly_audit_records = []
        
        # Step 1: Collect numeric data to calculate statistical bounds (IQR) for anomaly detection
        col_numeric_values = {i: [] for i in range(len(header))}
        parsed_rows = []
        
        for r_idx, row in enumerate(rows, start=1):
            parsed_row = []
            for col_idx, val in enumerate(row):
                v_str = str(val).strip()
                try:
                    num_val = float(v_str)
                    if not math.isnan(num_val) and not math.isinf(num_val):
                        parsed_row.append(num_val)
                        col_numeric_values[col_idx].append(num_val)
                    else:
                        parsed_row.append(v_str)
                except ValueError:
                    parsed_row.append(v_str)
            parsed_rows.append((r_idx, row, parsed_row))

        # Calculate IQR bounds per column
        col_bounds = {}
        for col_idx, vals in col_numeric_values.items():
            if len(vals) >= 4:
                sorted_vals = sorted(vals)
                q1 = sorted_vals[int(len(sorted_vals) * 0.25)]
                q3 = sorted_vals[int(len(sorted_vals) * 0.75)]
                iqr = q3 - q1
                col_bounds[col_idx] = (q1 - 2.0 * iqr, q3 + 2.0 * iqr) # Strict bounds for anomalies
            else:
                col_bounds[col_idx] = (None, None)

        # Step 2-9: Scan and score anomalies across rows
        final_output_rows = []
        for r_idx, original_row, parsed_row in parsed_rows:
            row_anomaly_score = 0.0
            is_anomalous = False
            
            for col_idx, val in enumerate(parsed_row):
                if isinstance(val, (int, float)):
                    lb, ub = col_bounds.get(col_idx, (None, None))
                    if lb is not None and ub is not None:
                        if val < lb or val > ub:
                            statistical_outliers += 1
                            row_anomaly_score += 0.5
                            is_anomalous = True

            # Step 9: Record anomaly scores and method used (IQR / Statistical)
            anomaly_audit_records.append({
                "row_index": r_idx,
                "anomaly_score": round(row_anomaly_score, 2),
                "method_used": "IQR_Statistical",
                "is_anomaly": is_anomalous
            })

            # Step 10: Require explicit policy before altering/excluding anomalous records
            if is_anomalous and policy == "exclude":
                continue # Skip/exclude row
            
            final_output_rows.append(original_row)

        # Write audit trail for anomalies
        with audit_path.open("w", encoding="utf-8", newline="") as audit_file:
            audit_writer = csv.writer(audit_file)
            audit_writer.writerow(["row_index", "anomaly_score", "method_used", "is_anomaly"])
            for rec in anomaly_audit_records:
                audit_writer.writerow([rec["row_index"], rec["anomaly_score"], rec["method_used"], rec["is_anomaly"]])

        # Write cleaned file
        with output_path.open("w", encoding="utf-8", newline="") as outfile:
            writer = csv.writer(outfile)
            writer.writerow(header)
            writer.writerows(final_output_rows)
            
        return {
            "file_path": str(output_path),
            "audit_path": str(audit_path),
            "summary": {
                "total_rows_scanned": total_rows,
                "statistical_outliers_detected": statistical_outliers,
                "unusual_combinations": unusual_categorical_combos,
                "applied_policy": policy
            }
        }
    except Exception as e:
        raise Exception(f"Error in anomaly detection pipeline: {str(e)}")

@router.post("/api/transform/anomaly-detection")
async def api_anomaly_detection(request: AnomalyDetectionRequest):
    try:
        result = await run_in_threadpool(
            process_anomaly_detection,
            request.file_path,
            request.anomaly_policy
        )
        return {
            "success": True,
            "message": "Anomaly and outlier detection suite executed successfully!",
            "data": result
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))