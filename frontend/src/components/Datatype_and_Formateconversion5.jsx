import { useState } from "react";
import "./styles/DatatypeAndFormatConversionStep.css"; // Adjust path if needed

export default function Datatype_and_Formatconversion5({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/type-inference", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to infer data types.");
      }
    } catch (err) {
      setError("Cannot connect to Type Inference API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="datatype-step-container">
      <h4 className="datatype-step-title">
        Step: Type Inference & Parsing Suite
      </h4>
      
      {!resultData ? (
        <div className="datatype-controls-wrapper">
          <p className="datatype-description">
            Infers integers, decimals, booleans, dates, timestamps, parses currencies/percentages, handles leading zeros, and detects mixed-type columns.
          </p>
          
          <button 
            className="datatype-run-btn" 
            onClick={handleRunPipeline} 
            disabled={loading}
          >
            {loading ? "Inferring Types..." : " 5 Data Types and Format Conversion →"}
          </button>
        </div>
      ) : (
        <div className="datatype-results-wrapper">
          <div className="datatype-success-msg">
            ✅ Type Inference Completed Successfully!
          </div>

          <div className="datatype-stats-grid">
            <div className="datatype-stat-card">
              <span className="datatype-stat-label">Integers</span>
              <span className="datatype-stat-value">
                {resultData.summary.inferred_types?.integer || 0}
              </span>
            </div>
            
            <div className="datatype-stat-card">
              <span className="datatype-stat-label">Decimals</span>
              <span className="datatype-stat-value">
                {resultData.summary.inferred_types?.decimal || 0}
              </span>
            </div>
            
            <div className="datatype-stat-card">
              <span className="datatype-stat-label">Booleans</span>
              <span className="datatype-stat-value">
                {resultData.summary.inferred_types?.boolean || 0}
              </span>
            </div>
            
            <div className="datatype-stat-card">
              <span className="datatype-stat-label">Dates</span>
              <span className="datatype-stat-value">
                {resultData.summary.inferred_types?.date || 0}
              </span>
            </div>
            
            <div className="datatype-stat-card">
              <span className="datatype-stat-label">Mixed Types</span>
              <span className={`datatype-stat-value ${resultData.summary.mixed_type_columns > 0 ? 'text-red' : 'text-emerald'}`}>
                {resultData.summary.mixed_type_columns}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="datatype-error-text">{error}</p>}
    </div>
  );
}