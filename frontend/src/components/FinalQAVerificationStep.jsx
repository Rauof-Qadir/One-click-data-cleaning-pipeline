import { useState } from "react";
import "./styles/FinalQAVerificationStep.css"; // Adjust path if needed

export default function FinalQAVerificationStep({ filePath, originalRows, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/final-qa-verification", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          file_path: filePath,
          original_row_count: originalRows || 0 
        }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to execute final QA verification.");
      }
    } catch (err) {
      setError("Cannot connect to Final QA API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="final-qa-step-container">
      <h4 className="final-qa-step-title">
        Step: Final QA, Verification & Compliance Suite
      </h4>
      
      {!resultData ? (
        <div className="final-qa-controls-wrapper">
          <p className="final-qa-description">
            Verifies primary keys, referential integrity, row/column counts, data loss safety, encoding, and compares quality metrics before export.
          </p>
          
          <button 
            className="final-qa-run-btn" 
            onClick={handleRunPipeline} 
            disabled={loading}
          >
            {loading ? "Running Final QA..." : "14 Final QA, Verification & Compliance →"}
          </button>
        </div>
      ) : (
        <div className="final-qa-results-wrapper">
          <div className="final-qa-success-msg">
            ✅ Final QA & Verification Completed Successfully!
          </div>

          <div className="final-qa-stats-grid">
            <div className="final-qa-stat-card">
              <span className="final-qa-stat-label">Final Rows</span>
              <span className="final-qa-stat-value">
                {resultData.summary.final_rows?.toLocaleString()}
              </span>
            </div>
            
            <div className="final-qa-stat-card">
              <span className="final-qa-stat-label">Final Columns</span>
              <span className="final-qa-stat-value">
                {resultData.summary.final_columns}
              </span>
            </div>
            
            <div className="final-qa-stat-card">
              <span className="final-qa-stat-label">PK Duplicates</span>
              <span className={`final-qa-stat-value ${resultData.summary.primary_key_duplicates > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.primary_key_duplicates}
              </span>
            </div>
            
            <div className="final-qa-stat-card">
              <span className="final-qa-stat-label">Status</span>
              <span className="final-qa-stat-value text-emerald uppercase">
                {resultData.summary.status}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="final-qa-error-text">{error}</p>}
    </div>
  );
}