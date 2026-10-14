import { useState } from "react";
import "./styles/NumericValidationStep.css"; // Adjust path if needed

export default function NumericValidationStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [strategy, setStrategy] = useState("flag");
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/numeric-validation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          file_path: filePath,
          strategy: strategy 
        }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to validate numeric data.");
      }
    } catch (err) {
      setError("Cannot connect to Numeric Validation API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="numeric-step-container">
      <h4 className="numeric-step-title">
        Step: Numeric Validation & Outlier Detection Suite
      </h4>
      
      {!resultData ? (
        <div className="numeric-controls-wrapper">
          <p className="numeric-description">
            Detects invalid strings, infinity, bounds, unit inconsistencies, and statistical outliers using IQR with robust strategies (flag, cap, exclude).
          </p>
          
          <div className="numeric-action-row">
            <select 
              value={strategy} 
              onChange={(e) => setStrategy(e.target.value)}
              className="numeric-select"
            >
              <option value="flag">Strategy: Flag Only</option>
              <option value="cap">Strategy: Cap / Winsorize</option>
              <option value="exclude">Strategy: Exclude Outliers</option>
            </select>

            <button 
              className="numeric-run-btn" 
              onClick={handleRunPipeline} 
              disabled={loading}
            >
              {loading ? "Validating Numerics..." : "8 Numeric Data Quality →"}
            </button>
          </div>
        </div>
      ) : (
        <div className="numeric-results-wrapper">
          <div className="numeric-success-msg">
            ✅ Numeric Validation Completed Successfully!
          </div>

          <div className="numeric-stats-grid">
            <div className="numeric-stat-card">
              <span className="numeric-stat-label">Scanned Rows</span>
              <span className="numeric-stat-value">
                {resultData.summary.total_rows_scanned?.toLocaleString()}
              </span>
            </div>
            
            <div className="numeric-stat-card">
              <span className="numeric-stat-label">Invalid Strings</span>
              <span className={`numeric-stat-value ${resultData.summary.invalid_numeric_strings > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.invalid_numeric_strings}
              </span>
            </div>
            
            <div className="numeric-stat-card">
              <span className="numeric-stat-label">Outliers Found</span>
              <span className={`numeric-stat-value ${resultData.summary.outliers_detected > 0 ? 'text-amber' : 'text-emerald'}`}>
                {resultData.summary.outliers_detected}
              </span>
            </div>
            
            <div className="numeric-stat-card">
              <span className="numeric-stat-label">Strategy</span>
              <span className="numeric-stat-value uppercase">
                {resultData.summary.validation_strategy}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="numeric-error-text">{error}</p>}
    </div>
  );
}