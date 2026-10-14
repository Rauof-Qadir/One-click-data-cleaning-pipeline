import { useState } from "react";
import "./styles/TextAndStringCleaningStep.css"; // Adjust path if needed

export default function Text_and_String_cleaning4({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [semanticCaps, setSemanticCaps] = useState(false);
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/text-standardization", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          file_path: filePath,
          semantic_capitalization: semanticCaps 
        }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to standardize text.");
      }
    } catch (err) {
      setError("Cannot connect to Text Standardization API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="text-cleaning-step-container">
      <h4 className="text-cleaning-step-title">
        Step: Advanced Text Standardization &amp; Cleaning
      </h4>
      
      {!resultData ? (
        <div className="text-cleaning-controls-wrapper">
          <p className="text-cleaning-description">
            Cleans whitespace, normalizes unicode, fixes mojibake, standardizes missing tokens (N/A, NULL), booleans, punctuation, and detects truncation/mixed scripts.
          </p>
          
          <div className="text-cleaning-action-row">
            <label className="text-cleaning-checkbox-label">
              <input 
                type="checkbox" 
                checked={semanticCaps} 
                onChange={(e) => setSemanticCaps(e.target.checked)} 
                className="text-cleaning-checkbox"
              />
              Enable Semantic Capitalization
            </label>

            <button 
              className="text-cleaning-run-btn" 
              onClick={handleRunPipeline} 
              disabled={loading}
            >
              {loading ? "Cleaning Text Cells..." : " 4 Text and String Cleaning →"}
            </button>
          </div>
        </div>
      ) : (
        <div className="text-cleaning-results-wrapper">
          <div className="text-cleaning-success-msg">
            ✅ Text Standardization Completed Successfully!
          </div>

          <div className="text-cleaning-stats-grid">
            <div className="text-cleaning-stat-card">
              <span className="text-cleaning-stat-label">Scanned</span>
              <span className="text-cleaning-stat-value">
                {resultData.summary.total_cells_scanned?.toLocaleString()} cells
              </span>
            </div>
            
            <div className="text-cleaning-stat-card">
              <span className="text-cleaning-stat-label">Spaces Fixed</span>
              <span className={`text-cleaning-stat-value ${resultData.summary.whitespace_issues_fixed > 0 ? 'text-amber' : 'text-emerald'}`}>
                {resultData.summary.whitespace_issues_fixed}
              </span>
            </div>
            
            <div className="text-cleaning-stat-card">
              <span className="text-cleaning-stat-label">Mojibake</span>
              <span className={`text-cleaning-stat-value ${resultData.summary.mojibake_detected > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.mojibake_detected}
              </span>
            </div>
            
            <div className="text-cleaning-stat-card">
              <span className="text-cleaning-stat-label">Truncated</span>
              <span className={`text-cleaning-stat-value ${resultData.summary.truncated_texts_detected > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.truncated_texts_detected}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="text-cleaning-error-text">{error}</p>}
    </div>
  );
}