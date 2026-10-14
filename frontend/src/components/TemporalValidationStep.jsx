import { useState } from "react";
import "./styles/TemporalValidationStep.css"; // Adjust path if needed

export default function TemporalValidationStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/temporal-validation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to validate temporal data.");
      }
    } catch (err) {
      setError("Cannot connect to Temporal Validation API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="temporal-step-container">
      <h4 className="temporal-step-title">
        Step: Temporal Validation & Date/Time Suite
      </h4>
      
      {!resultData ? (
        <div className="temporal-controls-wrapper">
          <p className="temporal-description">
            Standardizes valid dates, detects impossible calendar dates, flags ambiguous day/month orders, and validates business ranges.
          </p>
          
          <button 
            className="temporal-run-btn" 
            onClick={handleRunPipeline} 
            disabled={loading}
          >
            {loading ? "Validating Dates..." : "10 Date and Time Validation →"}
          </button>
        </div>
      ) : (
        <div className="temporal-results-wrapper">
          <div className="temporal-success-msg">
            ✅ Temporal Validation Completed Successfully!
          </div>

          <div className="temporal-stats-grid">
            <div className="temporal-stat-card">
              <span className="temporal-stat-label">Scanned Rows</span>
              <span className="temporal-stat-value">
                {resultData.summary.total_rows_scanned?.toLocaleString()}
              </span>
            </div>
            
            <div className="temporal-stat-card">
              <span className="temporal-stat-label">Dates Standardized</span>
              <span className="temporal-stat-value text-emerald">
                {resultData.summary.dates_standardized}
              </span>
            </div>
            
            <div className="temporal-stat-card">
              <span className="temporal-stat-label">Ambiguous Orders</span>
              <span className={`temporal-stat-value ${resultData.summary.ambiguous_orders_detected > 0 ? 'text-amber' : 'text-emerald'}`}>
                {resultData.summary.ambiguous_orders_detected}
              </span>
            </div>
            
            <div className="temporal-stat-card">
              <span className="temporal-stat-label">Invalid Dates</span>
              <span className={`temporal-stat-value ${resultData.summary.invalid_dates_detected > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.invalid_dates_detected}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="temporal-error-text">{error}</p>}
    </div>
  );
}