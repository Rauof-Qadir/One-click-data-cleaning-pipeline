import { useState } from "react";
import "./styles/AnomalyDetectionStep.css";

export default function AnomalyDetectionStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [policy, setPolicy] = useState("flag");
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/anomaly-detection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          file_path: filePath,
          anomaly_policy: policy 
        }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to detect anomalies.");
      }
    } catch (err) {
      setError("Cannot connect to Anomaly Detection API.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="anomaly-step-container">
      <h4 className="anomaly-step-title">
        Step: Anomaly & Outlier Detection Suite
      </h4>
      
      {!resultData ? (
        <div className="anomaly-controls-wrapper">
          <p className="anomaly-description">
            Detects statistical outliers, multivariate anomalies, distribution changes, records anomaly scores, and applies explicit policies.
          </p>
          
          <div className="anomaly-action-row">
            <select 
              value={policy} 
              onChange={(e) => setPolicy(e.target.value)}
              className="anomaly-select"
            >
              <option value="flag">Policy: Flag & Audit Only</option>
              <option value="exclude">Policy: Exclude Anomalies</option>
            </select>

            <button 
              className="anomaly-run-btn" 
              onClick={handleRunPipeline} 
              disabled={loading}
            >
              {loading ? "Scanning Anomalies..." : "13 Anomaly & Outlier Detection →"}
            </button>
          </div>
        </div>
      ) : (
        <div className="anomaly-results-wrapper">
          <div className="anomaly-success-msg">
            ✅ Anomaly Detection Completed Successfully!
          </div>

          <div className="anomaly-stats-grid">
            <div className="anomaly-stat-card">
              <span className="anomaly-stat-label">Scanned Rows</span>
              <span className="anomaly-stat-value">
                {resultData.summary.total_rows_scanned?.toLocaleString()}
              </span>
            </div>
            
            <div className="anomaly-stat-card">
              <span className="anomaly-stat-label">Outliers Found</span>
              <span className={`anomaly-stat-value ${resultData.summary.statistical_outliers_detected > 0 ? 'text-red' : 'text-green'}`}>
                {resultData.summary.statistical_outliers_detected}
              </span>
            </div>
            
            <div className="anomaly-stat-card">
              <span className="anomaly-stat-label">Policy Applied</span>
              <span className="anomaly-stat-value uppercase">
                {resultData.summary.applied_policy}
              </span>
            </div>
          </div>
        </div>
      )}

      {error && <p className="anomaly-error-text">{error}</p>}
    </div>
  );
}