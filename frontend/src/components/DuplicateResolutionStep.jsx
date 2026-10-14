import { useState } from "react";
import "./styles/DuplicateResolutionStep.css"; // Adjust path if needed

export default function DuplicateResolutionStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [strategy, setStrategy] = useState("keep_first");
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/duplicate-resolution", {
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
        setError(data.detail || "Failed to resolve duplicates.");
      }
    } catch (err) {
      setError("Cannot connect to Duplicate Resolution API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="duplicate-step-container">
      <h4 className="duplicate-step-title">
        Step: Duplicate Detection & Entity Resolution Suite
      </h4>
      
      {!resultData ? (
        <div className="duplicate-controls-wrapper">
          <p className="duplicate-description">
            Detects exact duplicates, business keys, near-duplicates, fuzzy matching, entity resolution, and handles keep-first/last strategies.
          </p>
          
          <div className="duplicate-action-row">
            <select 
              value={strategy} 
              onChange={(e) => setStrategy(e.target.value)}
              className="duplicate-select"
            >
              <option value="keep_first">Strategy: Keep First</option>
              <option value="keep_last">Strategy: Keep Last</option>
              <option value="best_record">Strategy: Best Record</option>
            </select>

            <button 
              className="duplicate-run-btn" 
              onClick={handleRunPipeline} 
              disabled={loading}
            >
              {loading ? "Resolving Duplicates..." : "7 Duplicate Detection and Record Identity →"}
            </button>
          </div>
        </div>
      ) : (
        <div className="duplicate-results-wrapper">
          <div className="duplicate-success-msg">
            ✅ Duplicate Resolution Completed Successfully!
          </div>

          <div className="duplicate-stats-grid">
            <div className="duplicate-stat-card">
              <span className="duplicate-stat-label">Scanned Rows</span>
              <span className="duplicate-stat-value">
                {resultData.summary.total_rows_scanned?.toLocaleString()}
              </span>
            </div>
            
            <div className="duplicate-stat-card">
              <span className="duplicate-stat-label">Duplicates Removed</span>
              <span className={`duplicate-stat-value ${resultData.summary.exact_duplicates_removed > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.exact_duplicates_removed}
              </span>
            </div>
            
            <div className="duplicate-stat-card">
              <span className="duplicate-stat-label">Unique Retained</span>
              <span className="duplicate-stat-value">
                {resultData.summary.unique_rows_retained?.toLocaleString()}
              </span>
            </div>
            
            <div className="duplicate-stat-card">
              <span className="duplicate-stat-label">Strategy</span>
              <span className="duplicate-stat-value uppercase">
                {resultData.summary.resolution_strategy}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="duplicate-error-text">{error}</p>}
    </div>
  );
}