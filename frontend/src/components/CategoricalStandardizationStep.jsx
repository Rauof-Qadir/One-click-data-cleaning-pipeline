import { useState } from "react";
import "./styles/CategoricalStandardizationStep.css"; // Adjust path if needed

export default function CategoricalStandardizationStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/categorical-standardization", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to standardize categories.");
      }
    } catch (err) {
      setError("Cannot connect to Categorical Standardization API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="categorical-step-container">
      <h4 className="categorical-step-title">
        Step: Categorical Standardization & Mapping Suite
      </h4>
      
      {!resultData ? (
        <div className="categorical-controls-wrapper">
          <p className="categorical-description">
            Standardizes spelling/whitespace, maps synonyms, detects rare categories, handles unknown/other labels distinctly, and flags ambiguous mappings.
          </p>
          
          <button 
            className="categorical-run-btn" 
            onClick={handleRunPipeline} 
            disabled={loading}
          >
            {loading ? "Standardizing Categories..." : "9 Categorical Data Quality →"}
          </button>
        </div>
      ) : (
        <div className="categorical-results-wrapper">
          <div className="categorical-success-msg">
            ✅ Categorical Standardization Completed Successfully!
          </div>

          <div className="categorical-stats-grid">
            <div className="categorical-stat-card">
              <span className="categorical-stat-label">Scanned Rows</span>
              <span className="categorical-stat-value">
                {resultData.summary.total_rows_scanned?.toLocaleString()}
              </span>
            </div>
            
            <div className="categorical-stat-card">
              <span className="categorical-stat-label">Synonyms Mapped</span>
              <span className="categorical-stat-value">
                {resultData.summary.synonyms_mapped}
              </span>
            </div>
            
            <div className="categorical-stat-card">
              <span className="categorical-stat-label">Rare Categories</span>
              <span className={`categorical-stat-value ${resultData.summary.rare_categories_detected > 0 ? 'text-amber' : 'text-emerald'}`}>
                {resultData.summary.rare_categories_detected}
              </span>
            </div>
            
            <div className="categorical-stat-card">
              <span className="categorical-stat-label">Ambiguous Flagged</span>
              <span className={`categorical-stat-value ${resultData.summary.ambiguous_mappings_flagged > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.ambiguous_mappings_flagged}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="categorical-error-text">{error}</p>}
    </div>
  );
}