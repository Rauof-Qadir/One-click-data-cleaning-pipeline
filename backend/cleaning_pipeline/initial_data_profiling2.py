import csv
import statistics
from pathlib import Path
from collections import defaultdict, Counter
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool
import traceback
from datetime import datetime

router = APIRouter()

class TransformRequest(BaseModel):
    file_path: str

# ==========================================
# PIPELINE STEP 11: Record Row & Column Count
# ==========================================
def count_rows_and_columns(file_path: str):
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found at path: {file_path}")
        
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            
            try:
                header = next(reader)
                column_count = len(header)
            except StopIteration:
                return {"rows": 0, "columns": 0}
            
            row_count = sum(1 for row in reader)
            
            return {
                "columns": column_count,
                "rows": row_count,
                "file_path": str(path)
            }
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")

# ==========================================
# PIPELINE STEP 12: Inspect Inferred Data Types
# ==========================================
def inspect_data_types(file_path: str):
    path = Path(file_path)
    types_dict = {}
    
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                return {}
            
            sample_data = defaultdict(list)
            for i, row in enumerate(reader):
                if i >= 100:
                    break
                for j, val in enumerate(row):
                    if j < len(headers):
                        sample_data[headers[j]].append(val)
                        
            for col in headers:
                values = sample_data.get(col, [])
                non_empty = [v.strip() for v in values if v.strip()]
                
                if not non_empty:
                    types_dict[col] = "Unknown / Empty"
                    continue
                    
                is_int, is_float, is_bool = True, True, True
                
                for v in non_empty:
                    v_lower = v.lower()
                    if is_bool and v_lower not in ['true', 'false', '0', '1', 'yes', 'no']:
                        is_bool = False
                    if is_int:
                        try:
                            int(v)
                        except ValueError:
                            is_int = False
                    if is_float:
                        try:
                            float(v)
                        except ValueError:
                            is_float = False
                            
                if is_bool:
                    types_dict[col] = "Boolean"
                elif is_int:
                    types_dict[col] = "Integer"
                elif is_float:
                    types_dict[col] = "Float"
                else:
                    types_dict[col] = "String/Text"
                    
        return types_dict
    except Exception as e:
        raise Exception(f"Error inspecting data types: {str(e)}")


# ==========================================
# PIPELINE STEP 13, 14, 15, 16 & 17: Quality, Empty Detect & Duplicates
# ==========================================
# ==========================================
# PIPELINE STEP 13-19: Safe Column Statistics & Categorical Profile
# ==========================================
def calculate_column_statistics(file_path: str):
    path = Path(file_path)
    stats = {}
    missing_tokens = {'na', 'n/a', 'null', 'none', '-', 'nan', 'undefined', '?'}
    
    empty_rows_count = 0
    empty_columns_list = []
    duplicate_rows_count = 0
    seen_row_hashes = set() 
    
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                return {}
            
            for h in headers:
                stats[h] = {
                    "blanks": 0, 
                    "missing_tokens": 0, 
                    "total_missing": 0,
                    "value_frequencies": Counter()
                }
                
            total_rows = 0
            for row in reader:
                total_rows += 1
                is_row_completely_empty = True
                
                try:
                    row_hash = hash(tuple(row))
                    if row_hash in seen_row_hashes:
                        duplicate_rows_count += 1
                    else:
                        seen_row_hashes.add(row_hash)
                except Exception:
                    pass # Hash error ignore karne ke liye
                
                for i, val in enumerate(row):
                    if i < len(headers):
                        col = headers[i]
                        cleaned_val = val.strip()
                        
                        if cleaned_val != "":
                            is_row_completely_empty = False
                        
                        if cleaned_val == "":
                            stats[col]["blanks"] += 1
                            stats[col]["total_missing"] += 1
                        elif cleaned_val.lower() in missing_tokens:
                            stats[col]["missing_tokens"] += 1
                            stats[col]["total_missing"] += 1
                            
                        stats[col]["value_frequencies"][cleaned_val] += 1
                        
                if is_row_completely_empty:
                    empty_rows_count += 1
                        
        for col in stats:
            freqs = stats[col]["value_frequencies"]
            cardinality = len(freqs)
            stats[col]["cardinality"] = cardinality
            
            if total_rows > 0 and stats[col]["blanks"] == total_rows:
                empty_columns_list.append(col)
                stats[col]["variance_status"] = "Empty"
            else:
                top_percent = 0
                if total_rows > 0 and freqs:
                    try:
                        top_value, top_count = freqs.most_common(1)[0]
                        top_percent = (top_count / total_rows) * 100
                    except Exception:
                        top_percent = 0
                    
                if cardinality <= 1:
                    stats[col]["variance_status"] = "Constant"
                elif top_percent >= 95:
                    stats[col]["variance_status"] = f"Near-Constant ({top_percent:.1f}%)"
                else:
                    stats[col]["variance_status"] = "Normal"
            
            # Safe Top and Rare Categories Extraction
            try:
                clean_freqs = {k: v for k, v in freqs.items() if k != ""}
                sorted_freqs = sorted(clean_freqs.items(), key=lambda x: x[1], reverse=True)
                
                stats[col]["top_categories"] = [{"value": str(k), "count": v} for k, v in sorted_freqs[:3]]
                
                if len(sorted_freqs) > 3:
                    stats[col]["rare_categories"] = [{"value": str(k), "count": v} for k, v in sorted_freqs[-3:]]
                else:
                    stats[col]["rare_categories"] = []
            except Exception:
                stats[col]["top_categories"] = []
                stats[col]["rare_categories"] = []
                
            del stats[col]["value_frequencies"]
            
        return {
            "column_details": stats,
            "empty_rows_count": empty_rows_count,
            "empty_columns": empty_columns_list,
            "duplicate_rows_count": duplicate_rows_count
        }
    except Exception as e:
        raise Exception(f"Error calculating column stats: {str(e)}")


def profile_numeric_columns(file_path: str, inferred_types: dict):
    path = Path(file_path)
    
    numeric_cols = [col for col, dtype in inferred_types.items() if dtype in ["Integer", "Float"]]
    
    if not numeric_cols:
        return {} 
        
    numeric_data = {col: [] for col in numeric_cols}
    
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            
            col_indices = {i: h for i, h in enumerate(headers) if h in numeric_cols}
            
            for row in reader:
                for i, val in enumerate(row):
                    if i in col_indices:
                        col = col_indices[i]
                        cleaned_val = val.strip()
                        if cleaned_val:
                            try:
                                numeric_data[col].append(float(cleaned_val))
                            except ValueError:
                                pass
                                
        numeric_stats = {}
        for col, values in numeric_data.items():
            if not values:
                continue
                
            values.sort()
            n = len(values)
            
            min_val = values[0]
            max_val = values[-1]
            mean_val = sum(values) / n
            median_val = statistics.median(values)
            std_dev = statistics.stdev(values) if n > 1 else 0
            q1 = values[n // 4]
            q3 = values[(n * 3) // 4]
            
            numeric_stats[col] = {
                "min": round(min_val, 2),
                "max": round(max_val, 2),
                "mean": round(mean_val, 2),
                "median": round(median_val, 2),
                "q1": round(q1, 2),
                "q3": round(q3, 2),
                "std_dev": round(std_dev, 2)
            }
            
        return numeric_stats
    except Exception as e:
        raise Exception(f"Error profiling numeric data: {str(e)}")
    

# ==========================================
# PIPELINE STEP 18: Profile Numeric Columns
# ==========================================
# ==========================================
# PIPELINE STEP 13, 14, 15, 16, 17 & 19: Quality, Duplicates & Categorical Profile
# ==========================================
def calculate_column_statistics(file_path: str):
    path = Path(file_path)
    stats = {}
    missing_tokens = {'na', 'n/a', 'null', 'none', '-', 'nan', 'undefined', '?'}
    
    empty_rows_count = 0
    empty_columns_list = []
    duplicate_rows_count = 0
    seen_row_hashes = set() 
    
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            try:
                headers = next(reader)
            except StopIteration:
                return {}
            
            for h in headers:
                stats[h] = {
                    "blanks": 0, 
                    "missing_tokens": 0, 
                    "total_missing": 0,
                    "value_frequencies": Counter()
                }
                
            total_rows = 0
            for row in reader:
                total_rows += 1
                is_row_completely_empty = True
                
                row_hash = hash(tuple(row))
                if row_hash in seen_row_hashes:
                    duplicate_rows_count += 1
                else:
                    seen_row_hashes.add(row_hash)
                
                for i, val in enumerate(row):
                    if i < len(headers):
                        col = headers[i]
                        cleaned_val = val.strip()
                        
                        if cleaned_val != "":
                            is_row_completely_empty = False
                        
                        if cleaned_val == "":
                            stats[col]["blanks"] += 1
                            stats[col]["total_missing"] += 1
                        elif cleaned_val.lower() in missing_tokens:
                            stats[col]["missing_tokens"] += 1
                            stats[col]["total_missing"] += 1
                            
                        stats[col]["value_frequencies"][cleaned_val] += 1
                        
                if is_row_completely_empty:
                    empty_rows_count += 1
                        
        for col in stats:
            freqs = stats[col]["value_frequencies"]
            cardinality = len(freqs)
            stats[col]["cardinality"] = cardinality
            
            if total_rows > 0 and stats[col]["blanks"] == total_rows:
                empty_columns_list.append(col)
                stats[col]["variance_status"] = "Empty"
            else:
                top_percent = 0
                if total_rows > 0 and freqs:
                    top_value, top_count = freqs.most_common(1)[0]
                    top_percent = (top_count / total_rows) * 100
                    
                if cardinality <= 1:
                    stats[col]["variance_status"] = "Constant"
                elif top_percent >= 95:
                    stats[col]["variance_status"] = f"Near-Constant ({top_percent:.1f}%)"
                else:
                    stats[col]["variance_status"] = "Normal"
            
            # =======================================
            # STEP 19: Categorical Frequencies & Rare Categories
            # =======================================
            # Khali strings ("") ko nikal kar baqi data ki frequencies banayen
            clean_freqs = {k: v for k, v in freqs.items() if k != ""}
            sorted_freqs = sorted(clean_freqs.items(), key=lambda x: x[1], reverse=True)
            
            # Top 3 values (Sab se zyada aane wali)
            stats[col]["top_categories"] = [{"value": k, "count": v} for k, v in sorted_freqs[:3]]
            
            # Rare values (Sab se kam aane wali, sirf tab jab column mein 3 se zyada unique values hon)
            if len(sorted_freqs) > 3:
                stats[col]["rare_categories"] = [{"value": k, "count": v} for k, v in sorted_freqs[-3:]]
            else:
                stats[col]["rare_categories"] = []
                
            del stats[col]["value_frequencies"] # Memory free karein
            
        return {
            "column_details": stats,
            "empty_rows_count": empty_rows_count,
            "empty_columns": empty_columns_list,
            "duplicate_rows_count": duplicate_rows_count
        }
    except Exception as e:
        raise Exception(f"Error calculating column stats: {str(e)}")



def profile_temporal_columns(file_path: str, inferred_types: dict):
    """
    Yeh function date/timestamp columns ko scan kar ke:
    1. Earliest (Min) aur Latest (Max) date nikalta hai.
    2. Temporal gaps (misconfigured ya missing days) check karta hai.
    """
    path = Path(file_path)
    
    # Simple regex ya format check se date columns dhoond sakte hain, 
    # ya hum un columns ko target karein jinke naam mein 'date', 'time', 'created', 'at' ho 
    # ya phir values par date parsing try karein.
    
    temporal_stats = {}
    
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            
            # Date format patterns jo aam tor par use hote hain
            date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"]
            
            col_data = {h: [] for h in headers}
            
            # Sample rows par check karein ke kon sa column date format support karta hai
            sample_count = 0
            for row in reader:
                sample_count += 1
                if sample_count > 200: # Fast check ke liye shuru ki 200 rows
                    break
                for i, val in enumerate(row):
                    if i < len(headers):
                        cleaned = val.strip()
                        if cleaned:
                            col_data[headers[i]].append(cleaned)
                            
            # Har column ko test karein ke kya yeh date hai
            valid_date_cols = []
            for col, values in col_data.items():
                if not values:
                    continue
                matched_format = None
                parsed_dates = []
                
                for fmt in date_formats:
                    success_count = 0
                    temp_dates = []
                    for v in values[:20]: # 20 values par test karein
                        try:
                            dt = datetime.strptime(v, fmt)
                            temp_dates.append(dt)
                            success_count += 1
                        except ValueError:
                            break
                    if success_count >= min(5, len(values)):
                        matched_format = fmt
                        break
                        
                if matched_format:
                    valid_date_cols.append((col, matched_format))
                    
            # Agar koi date column mila, tou poori file par range nikalein
            if valid_date_cols:
                with path.open("r", encoding="utf-8") as inner_f:
                    inner_reader = csv.reader(inner_f)
                    inner_headers = next(inner_reader, [])
                    
                    full_date_data = {col: [] for col, _ in valid_date_cols}
                    col_idx_map = {inner_headers.index(col): (col, fmt) for col, fmt in valid_date_cols if col in inner_headers}
                    
                    for row in inner_reader:
                        for i, val in enumerate(row):
                            if i in col_idx_map:
                                col_name, fmt = col_idx_map[i]
                                try:
                                    dt = datetime.strptime(val.strip(), fmt)
                                    full_date_data[col_name].append(dt)
                                except ValueError:
                                    pass
                                    
                for col, dates in full_date_data.items():
                    if dates:
                        dates.sort()
                        earliest = dates[0]
                        latest = dates[-1]
                        
                        # Temporal Gap check (agar koi bara gap ho)
                        max_gap_days = 0
                        if len(dates) > 1:
                            gaps = [(dates[idx+1] - dates[idx]).days for idx in range(len(dates)-1)]
                            max_gap_days = max(gaps) if gaps else 0
                            
                        temporal_stats[col] = {
                            "earliest": earliest.strftime("%Y-%m-%d"),
                            "latest": latest.strftime("%Y-%m-%d"),
                            "total_span_days": (latest - earliest).days,
                            "max_temporal_gap_days": max_gap_days
                        }
                        
        return temporal_stats
    except Exception as e:
        return {}
    

# ==========================================
# PIPELINE STEP 21: Detect Suspicious Distributions & Anomalies
# ==========================================
def detect_numeric_anomalies(file_path: str, inferred_types: dict):
    """
    Yeh function numeric columns mein Interquartile Range (IQR) method 
    use kar ke potential anomalies (outliers) count karega.
    """
    path = Path(file_path)
    numeric_cols = [col for col, dtype in inferred_types.items() if dtype in ["Integer", "Float"]]
    
    if not numeric_cols:
        return {}
        
    numeric_data = {col: [] for col in numeric_cols}
    
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            col_indices = {i: h for i, h in enumerate(headers) if h in numeric_cols}
            
            for row in reader:
                for i, val in enumerate(row):
                    if i in col_indices:
                        col = col_indices[i]
                        cleaned = val.strip()
                        if cleaned:
                            try:
                                numeric_data[col].append(float(cleaned))
                            except ValueError:
                                pass
                                
        anomaly_stats = {}
        for col, values in numeric_data.items():
            if len(values) < 5:
                continue
                
            values.sort()
            n = len(values)
            
            # Q1 aur Q3 nikalna
            q1 = values[n // 4]
            q3 = values[(n * 3) // 4]
            iqr = q3 - q1
            
            # Outlier boundaries (Tukey's fences)
            lower_bound = q1 - (1.5 * iqr)
            upper_bound = q3 + (1.5 * iqr)
            
            # Outliers count karein
            outliers = [v for v in values if v < lower_bound or v > upper_bound]
            outlier_count = len(outliers)
            
            if outlier_count > 0:
                anomaly_stats[col] = {
                    "outlier_count": outlier_count,
                    "outlier_percentage": round((outlier_count / n) * 100, 2),
                    "lower_bound": round(lower_bound, 2),
                    "upper_bound": round(upper_bound, 2)
                }
                
        return anomaly_stats
    except Exception as e:
        return {}

    

# ==========================================
# PIPELINE STEP 22: Detect High-Cardinality & Potential Keys
# ==========================================
def detect_potential_keys(stats_result: dict, total_rows: int):
    """
    Yeh function check karta hai ke kis column ki cardinality 
    total rows ke barabar ya qareeb hai, jisse woh Potential Key ya ID ban sakta hai.
    """
    potential_keys = []
    
    if total_rows <= 0:
        return []
        
    column_details = stats_result.get("column_details", {})
    
    for col, info in column_details.items():
        cardinality = info.get("cardinality", 0)
        
        # Agar unique values ka percentage 98% ya us se zyada hai, tou woh Potential Key hai
        uniqueness_ratio = (cardinality / total_rows) * 100
        
        if uniqueness_ratio >= 98.0 and total_rows > 1:
            potential_keys.append({
                "column": col,
                "cardinality": cardinality,
                "uniqueness_percentage": round(uniqueness_ratio, 2)
            })
            
    return potential_keys


# ==========================================
# PIPELINE STEP 23: Generate Baseline Data-Quality Score
# ==========================================
def calculate_data_quality_score(counts: dict, stats_result: dict, anomaly_profiles: dict, total_rows: int, total_cols: int):
    """
    Yeh function mukhtalif data quality metrics (missing values, duplicates, empty elements) 
    ke base par 0-100 ka overall score aur component breakdown generate karta hai.
    """
    if total_rows <= 0 or total_cols <= 0:
        return {"score": 100, "components": {}}
        
    column_details = stats_result.get("column_details", {})
    
    # 1. Missing Values Penalty
    total_cells = total_rows * total_cols
    total_missing_cells = sum(info.get("total_missing", 0) for info in column_details.values())
    missing_penalty = min(30.0, (total_missing_cells / total_cells) * 30) if total_cells > 0 else 0
    
    # 2. Duplicate Rows Penalty
    dup_count = stats_result.get("duplicate_rows_count", 0)
    dup_penalty = min(25.0, (dup_count / total_rows) * 25) if total_rows > 0 else 0
    
    # 3. Empty Rows & Columns Penalty
    empty_rows = stats_result.get("empty_rows_count", 0)
    empty_cols = len(stats_result.get("empty_columns", []))
    empty_penalty = min(20.0, ((empty_rows + empty_cols) / (total_rows + total_cols)) * 20) if (total_rows + total_cols) > 0 else 0
    
    # 4. Anomalies / Outliers Penalty
    total_outliers = sum(anom.get("outlier_count", 0) for anom in anomaly_profiles.values())
    anomaly_penalty = min(15.0, (total_outliers / total_cells) * 15) if total_cells > 0 else 0
    
    # 5. Constant Columns Penalty
    constant_cols = sum(1 for info in column_details.values() if "Constant" in info.get("variance_status", ""))
    constant_penalty = min(10.0, (constant_cols / total_cols) * 10) if total_cols > 0 else 0
    
    # Final Score Calculation (100 mein se penalties minus karna)
    final_score = max(0.0, 100.0 - (missing_penalty + dup_penalty + empty_penalty + anomaly_penalty + constant_penalty))
    
    return {
        "overall_score": round(final_score, 1),
        "components": {
            "completeness": round(max(0.0, 100.0 - (missing_penalty / 30.0) * 100), 1),
            "uniqueness": round(max(0.0, 100.0 - (dup_penalty / 25.0) * 100), 1),
            "structural_integrity": round(max(0.0, 100.0 - (empty_penalty / 20.0) * 100), 1),
            "validity": round(max(0.0, 100.0 - (anomaly_penalty / 15.0) * 100), 1),
            "variance": round(max(0.0, 100.0 - (constant_penalty / 10.0) * 100), 1)
        }
    }

@router.post("/api/transform/record-counts")
async def analyze_dataset_structure(request: TransformRequest):
    try:
        counts = await run_in_threadpool(count_rows_and_columns, request.file_path)
        inferred_types = await run_in_threadpool(inspect_data_types, request.file_path)
        stats_result = await run_in_threadpool(calculate_column_statistics, request.file_path)
        numeric_profiles = await run_in_threadpool(profile_numeric_columns, request.file_path, inferred_types)
        temporal_profiles = await run_in_threadpool(profile_temporal_columns, request.file_path, inferred_types)
        anomaly_profiles = await run_in_threadpool(detect_numeric_anomalies, request.file_path, inferred_types)
        potential_keys = detect_potential_keys(stats_result, counts["rows"])
        
        # 🔴 NAYA STEP 23 CALL KAREIN
        quality_score = calculate_data_quality_score(counts, stats_result, anomaly_profiles, counts["rows"], counts["columns"])
        
        counts["data_types"] = inferred_types
        counts["column_stats"] = stats_result["column_details"]
        counts["empty_rows_count"] = stats_result["empty_rows_count"]
        counts["empty_columns"] = stats_result["empty_columns"]
        counts["duplicate_rows_count"] = stats_result["duplicate_rows_count"]
        counts["numeric_profiles"] = numeric_profiles
        counts["temporal_profiles"] = temporal_profiles
        counts["anomaly_profiles"] = anomaly_profiles
        counts["potential_keys"] = potential_keys
        counts["quality_score"] = quality_score # Naya score data bhej diya
        
        return {
            "success": True,
            "message": "Dataset structure analyzed completely!",
            "data": counts
        }
    except Exception as exc:
        print("--- ERROR IN TRANSFORMATION PIPELINE ---")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(exc))