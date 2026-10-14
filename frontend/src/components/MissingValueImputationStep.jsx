import { useState } from "react";
import "./styles/MissingValueImputationStep.css"; // Adjust path if needed

export default function MissingValueImputationStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [strategy, setStrategy] = useState("mean");
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/missing-imputation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          file_path: filePath,
          impute_strategy: strategy 
        }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to process missing values.");
      }
    } catch (err) {
      setError("Cannot connect to Missing Imputation API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="missing-step-container">
      <h4 className="missing-step-title">
        Step: Missing Value Analysis & Imputation Suite
      </h4>
      
      {!resultData ? (
        <div className="missing-controls-wrapper">
          <p className="missing-description">
            Detects true nulls, placeholders (?, -, unknown), analyzes missingness thresholds, applies smart imputation strategies, and documents deletions.
          </p>
          
          <div className="missing-action-row">
            <select 
              value={strategy} 
              onChange={(e) => setStrategy(e.target.value)}
              className="missing-select"
            >
              <option value="mean">Strategy: Mean / Mode</option>
              <option value="median">Strategy: Median</option>
              <option value="none">Strategy: Flag & Review Only</option>
            </select>

            <button 
              className="missing-run-btn" 
              onClick={handleRunPipeline} 
              disabled={loading}
            >
              {loading ? "Processing Missing Values..." : "6 Missing Value and Incomplete Data Handling →"}
            </button>
          </div>
        </div>
      ) : (
        <div className="missing-results-wrapper">
          <div className="missing-success-msg">
            ✅ Missing Value Imputation Completed Successfully!
          </div>

          <div className="missing-stats-grid">
            <div className="missing-stat-card">
              <span className="missing-stat-label">Scanned Rows</span>
              <span className="missing-stat-value">
                {resultData.summary.total_rows_scanned?.toLocaleString()}
              </span>
            </div>
            
            <div className="missing-stat-card">
              <span className="missing-stat-label">Missing / Placeholders</span>
              <span className={`missing-stat-value ${resultData.summary.missing_values_detected > 0 ? 'text-amber' : 'text-emerald'}`}>
                {resultData.summary.missing_values_detected}
              </span>
            </div>
            
            <div className="missing-stat-card">
              <span className="missing-stat-label">Empty Rows Dropped</span>
              <span className="missing-stat-value">
                {resultData.summary.fully_empty_rows_dropped}
              </span>
            </div>
            
            <div className="missing-stat-card">
              <span className="missing-stat-label">Strategy</span>
              <span className="missing-stat-value uppercase">
                {resultData.summary.imputation_strategy_applied}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="missing-error-text">{error}</p>}
    </div>
  );
}