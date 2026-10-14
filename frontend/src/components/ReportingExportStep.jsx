import { useState } from "react";
import "./styles/ReportingExportStep.css"; // Adjust path if needed

export default function ReportingExportStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [resultData, setResultData] = useState(null);
  const [error, setError] = useState("");

  const handleRunPipeline = async () => {
    if (!filePath) return;
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/transform/reporting-export", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_path: filePath }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        setResultData(data.data);
        if (onProcessed) onProcessed(data.data.file_path);
      } else {
        setError(data.detail || "Failed to generate report and export.");
      }
    } catch (err) {
      setError("Cannot connect to Reporting & Export API.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!resultData?.file_path) return;
    const downloadUrl = `http://localhost:8000/api/download/cleaned-file?file_path=${encodeURIComponent(resultData.file_path)}`;
    window.open(downloadUrl, '_blank');
  };

  return (
    <div className="reporting-step-container">
      <h4 className="reporting-step-title">
        Step: Reporting, Export & Compliance Suite
      </h4>
      
      {!resultData ? (
        <div className="reporting-controls-wrapper">
          <p className="reporting-description">
            Generates human-readable reports, machine-readable JSON metrics, audit trails, and provides a secure download link for your cleaned dataset.
          </p>
          
          <button 
            className="reporting-run-btn" 
            onClick={handleRunPipeline} 
            disabled={loading}
          >
            {loading ? "Generating Report..." : "15 Reporting, Export & Compliance →"}
          </button>
        </div>
      ) : (
        <div className="reporting-results-wrapper">
          <div className="reporting-success-msg">
            ✅ Cleaning Report Generated &amp; Export Ready!
          </div>

          <div className="reporting-stats-grid">
            <div className="reporting-stat-card">
              <span className="reporting-stat-label">Total Rows</span>
              <span className="reporting-stat-value">
                {resultData.summary.total_rows?.toLocaleString()}
              </span>
            </div>
            
            <div className="reporting-stat-card">
              <span className="reporting-stat-label">Total Columns</span>
              <span className="reporting-stat-value">
                {resultData.summary.total_columns}
              </span>
            </div>
            
            <div className="reporting-stat-card">
              <span className="reporting-stat-label">JSON Report</span>
              <span className="reporting-stat-value text-emerald">
                Generated
              </span>
            </div>
            
            <div className="reporting-stat-card">
              <span className="reporting-stat-label">Status</span>
              <span className="reporting-stat-value text-emerald uppercase">
                Ready
              </span>
            </div>
          </div>

          {/* Download Cleaned CSV Button */}
          <button 
            className="reporting-download-btn"
            onClick={handleDownload}
          >
            <span className="reporting-download-icon" aria-hidden="true">📥</span>
            Download Cleaned CSV File
          </button>
        </div>
      )}

      {error && <p className="reporting-error-text">{error}</p>}
    </div>
  );
}