import { useState } from "react";
import "./styles/DomainValidationStep.css"; // Adjust path if needed

export default function DomainValidationStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/domain-validation", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to validate domain-specific rules.");
      }
    } catch (err) {
      setError("Cannot connect to Domain Validation API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="domain-step-container">
      <h4 className="domain-step-title">
        Step: Advanced Domain-Specific Validation Suite
      </h4>
      
      {!resultData ? (
        <div className="domain-controls-wrapper">
          <p className="domain-description">
            Validates email syntax, postal codes, UUIDs, currency codes, geo coordinates, pricing totals, and distinguishes hard failures from warnings.
          </p>
          
          <button 
            className="domain-run-btn" 
            onClick={handleRunPipeline} 
            disabled={loading}
          >
            {loading ? "Validating Domain Rules..." : "11 Domain-Specific Validation →"}
          </button>
        </div>
      ) : (
        <div className="domain-results-wrapper">
          <div className="domain-success-msg">
            ✅ Domain Validation Completed Successfully!
          </div>

          <div className="domain-stats-grid">
            <div className="domain-stat-card">
              <span className="domain-stat-label">Scanned Rows</span>
              <span className="domain-stat-value">
                {resultData.summary.total_rows_scanned?.toLocaleString()}
              </span>
            </div>
            
            <div className="domain-stat-card">
              <span className="domain-stat-label">Valid Emails</span>
              <span className="domain-stat-value">
                {resultData.summary.emails_validated}
              </span>
            </div>
            
            <div className="domain-stat-card">
              <span className="domain-stat-label">Valid UUIDs</span>
              <span className="domain-stat-value">
                {resultData.summary.uuids_validated}
              </span>
            </div>
            
            <div className="domain-stat-card">
              <span className="domain-stat-label">Hard Failures</span>
              <span className={`domain-stat-value ${resultData.summary.hard_failures > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.hard_failures}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="domain-error-text">{error}</p>}
    </div>
  );
}