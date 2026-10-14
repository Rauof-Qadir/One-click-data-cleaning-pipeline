import { useState } from "react";
import "./styles/CrossColumnConsistencyStep.css"; // Adjust path if needed

export default function CrossColumnConsistencyStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/cross-column-consistency", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to check cross-column consistency.");
      }
    } catch (err) {
      setError("Cannot connect to Cross-Column Consistency API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="cross-column-step-container">
      <h4 className="cross-column-step-title">
        Step: Cross-Column & Business Logic Suite
      </h4>
      
      {!resultData ? (
        <div className="cross-column-controls-wrapper">
          <p className="cross-column-description">
            Checks arithmetic relationships, subtotals vs totals, quantity × unit price = revenue, balances, and incompatible field combinations.
          </p>
          
          <button 
            className="cross-column-run-btn" 
            onClick={handleRunPipeline} 
            disabled={loading}
          >
            {loading ? "Checking Logic..." : "12 Cross-Column & Business Consistency →"}
          </button>
        </div>
      ) : (
        <div className="cross-column-results-wrapper">
          <div className="cross-column-success-msg">
            ✅ Cross-Column Consistency Checked Successfully!
          </div>

          <div className="cross-column-stats-grid">
            <div className="cross-column-stat-card">
              <span className="cross-column-stat-label">Scanned Rows</span>
              <span className="cross-column-stat-value">
                {resultData.summary.total_rows_scanned?.toLocaleString()}
              </span>
            </div>
            
            <div className="cross-column-stat-card">
              <span className="cross-column-stat-label">Math Mismatches</span>
              <span className={`cross-column-stat-value ${resultData.summary.arithmetic_mismatches > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.arithmetic_mismatches}
              </span>
            </div>
            
            <div className="cross-column-stat-card">
              <span className="cross-column-stat-label">Incompatible</span>
              <span className="cross-column-stat-value">
                {resultData.summary.incompatible_field_combinations}
              </span>
            </div>
            
            <div className="cross-column-stat-card">
              <span className="cross-column-stat-label">Contradictions</span>
              <span className="cross-column-stat-value">
                {resultData.summary.contradictory_records}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="cross-column-error-text">{error}</p>}
    </div>
  );
}