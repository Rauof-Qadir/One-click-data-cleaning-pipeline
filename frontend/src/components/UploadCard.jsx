import { useState } from "react";
import "./styles/UploadCard.css";

export default function UploadCard({
  file,
  isUploading,
  progress,
  stepIndex,
  processingSteps,
  status,
  result,
  error,
  inputRef,
  selectFile,
  uploadFile,
  reset,
}) {
  const [isDragging, setIsDragging] = useState(false);

  const safeProgress = Math.min(100, Math.max(0, Number(progress) || 0));
  const currentStep = processingSteps?.[stepIndex];

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);

    if (!isUploading && event.dataTransfer.files?.length > 0) {
      selectFile(event.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (event) => {
    const selectedFile = event.target.files?.[0];

    if (selectedFile) {
      selectFile(selectedFile);
    }

    event.target.value = "";
  };

  return (
    <section
      className={`upload-card ${isUploading ? "is-uploading" : ""} ${
        isDragging ? "is-dragging" : ""
      } ${status === "success" ? "has-success" : ""} ${
        status === "error" ? "has-error" : ""
      }`}
      onDragEnter={(event) => {
        event.preventDefault();
        if (!isUploading) setIsDragging(true);
      }}
      onDragOver={(event) => event.preventDefault()}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setIsDragging(false);
        }
      }}
      onDrop={handleDrop}
    >
      <div className="upload-card-glow" aria-hidden="true" />

      {/* Header */}
      <div className="card-top">
        <div className="upload-heading">
          <div className="upload-heading-icon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 16V4" />
              <path d="m7 9 5-5 5 5" />
              <path d="M5 14v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5" />
            </svg>
          </div>

          <div>
            <h2>Upload your dataset</h2>
            <p>Turn your raw CSV into analysis-ready data.</p>
          </div>
        </div>

        <div className="file-type">
          <span className="file-type-dot" />
          CSV FILE
        </div>
      </div>

      <input
        ref={inputRef}
        className="upload-input"
        type="file"
        accept=".csv,text/csv"
        hidden
        disabled={isUploading}
        onChange={handleFileChange}
      />

      {/* Empty state / drop zone */}
      {!file ? (
        <button
          className="drop-zone"
          type="button"
          disabled={isUploading}
          onClick={() => inputRef.current?.click()}
          aria-label="Choose a CSV file from your computer"
        >
          <span className="drop-zone-decoration drop-decoration-one" />
          <span className="drop-zone-decoration drop-decoration-two" />

          <span className="upload-illustration" aria-hidden="true">
            <span className="upload-illustration-back">
              <svg viewBox="0 0 24 24" fill="none">
                <path
                  d="M5 4h10l4 4v12H5z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
                <path
                  d="M15 4v5h4M8 13h8M8 16h8"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            </span>

            <span className="upload-illustration-front">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M12 16V4" />
                <path d="m7 9 5-5 5 5" />
                <path d="M5 14v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5" />
              </svg>
            </span>
          </span>

          <strong className="drop-zone-title">
            {isDragging ? "Drop your file here" : "Drop your dataset here"}
          </strong>

          <span className="drop-zone-subtitle">
            or <span className="browse-highlight">browse files</span> from
            your computer
          </span>

          <span className="drop-zone-action">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 16V4" />
              <path d="m7 9 5-5 5 5" />
              <path d="M5 14v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5" />
            </svg>
            Choose CSV file
          </span>

          <span className="drop-zone-hint">
            <span>.CSV</span>
            CSV files only · No frontend size limit
          </span>
        </button>
      ) : (
        /* Selected file */
        <div className="selected-file">
          <div className="selected-file-main">
            <div className="csv-icon" aria-hidden="true">
              <svg viewBox="0 0 32 36" fill="none">
                <path
                  d="M5 1.5h14l8 8V32a2.5 2.5 0 0 1-2.5 2.5h-17A2.5 2.5 0 0 1 5 32z"
                  fill="currentColor"
                  opacity=".13"
                />
                <path
                  d="M19 1.5v8h8"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
                <path
                  d="M5 1.5h14l8 8V32a2.5 2.5 0 0 1-2.5 2.5h-17A2.5 2.5 0 0 1 5 32z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinejoin="round"
                />
                <path
                  d="M9 18h14M9 22h14M9 26h14"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                />
              </svg>
              <span>CSV</span>
            </div>

            <div className="file-details">
              <strong title={file.name}>{file.name}</strong>
              <div className="file-meta">
                <span>
                  {(file.size / 1024 ** 2).toFixed(2)} MB
                </span>
                <span className="file-meta-separator" />
                <span className="file-ready-label">
                  <span className="file-ready-dot" />
                  File selected
                </span>
              </div>
            </div>
          </div>

          {!isUploading && (
            <button
              className="remove-btn"
              onClick={reset}
              type="button"
              aria-label="Remove selected file"
              title="Remove file"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                aria-hidden="true"
              >
                <path d="m6 6 12 12M18 6 6 18" />
              </svg>
            </button>
          )}
        </div>
      )}

      {/* Upload / processing progress */}
      {isUploading && (
        <div className="progress-section" aria-live="polite">
          <div className="progress-heading">
            <div className="progress-status-icon">
              <span className="progress-spinner" />
            </div>

            <div className="progress-text">
              <strong>
                {safeProgress < 100
                  ? "Uploading your dataset"
                  : currentStep || "Finalizing analysis"}
              </strong>
              <span>
                {safeProgress < 100
                  ? "Securely transferring your CSV..."
                  : "Upload complete. Processing your data..."}
              </span>
            </div>

            <strong className="progress-percentage">
              {safeProgress < 100 ? `${Math.round(safeProgress)}%` : "✓"}
            </strong>
          </div>

          <div
            className="progress-track"
            role="progressbar"
            aria-label="File upload progress"
            aria-valuenow={Math.round(safeProgress)}
            aria-valuemin={0}
            aria-valuemax={100}
          >
            <div
              className={`progress-fill ${
                safeProgress >= 100 ? "processing-pulse" : ""
              }`}
              style={{ width: `${safeProgress}%` }}
            />
          </div>

          {safeProgress >= 100 && (
            <div className="processing-note">
              <span className="processing-note-dot" />
              Your data is being analyzed. This may take a moment.
            </div>
          )}
        </div>
      )}

      {/* Successful upload */}
      {status === "success" && result && (
        <div className="message success-message" role="status">
          <div className="message-icon success-icon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.3"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="m5 12 4 4L19 6" />
            </svg>
          </div>

          <div className="message-content">
            <div className="message-title-row">
              <strong>Analysis completed!</strong>
              <span className="success-pill">SUCCESS</span>
            </div>

            <p>Your dataset has been successfully analyzed.</p>

            <div className="stats">
              <div className="result-stat">
                <span className="result-stat-label">Total rows</span>
                <strong>{result.rows.toLocaleString()}</strong>
              </div>

              <div className="result-stat">
                <span className="result-stat-label">Total columns</span>
                <strong>{result.columns.toLocaleString()}</strong>
              </div>
            </div>

            {(result.encoding ||
              result.delimiter ||
              result.quotechar ||
              result.escapechar) && (
              <div className="result-metadata">
                <span className="metadata-heading">FILE METADATA</span>

                <div className="metadata-badges">
                  {result.encoding && (
                    <span className="metadata-badge">
                      <span>Encoding</span>
                      <strong>{result.encoding}</strong>
                    </span>
                  )}

                  {result.delimiter && (
                    <span className="metadata-badge">
                      <span>Delimiter</span>
                      <strong>
                        {result.delimiter === "\t"
                          ? "Tab"
                          : result.delimiter === " "
                            ? "Space"
                            : result.delimiter}
                      </strong>
                    </span>
                  )}

                  {result.quotechar && (
                    <span className="metadata-badge">
                      <span>Quote</span>
                      <strong>{result.quotechar}</strong>
                    </span>
                  )}

                  {result.escapechar && (
                    <span className="metadata-badge">
                      <span>Escape</span>
                      <strong>
                        {result.escapechar === "\t"
                          ? "Tab"
                          : result.escapechar}
                      </strong>
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Error state */}
      {status === "error" && error && (
        <div className="message error-message" role="alert">
          <div className="message-icon error-icon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 9v4" />
              <path d="M12 17h.01" />
              <circle cx="12" cy="12" r="9" />
            </svg>
          </div>

          <div className="message-content">
            <strong>We couldn't process your dataset</strong>
            <p>{error}</p>
            <span className="error-hint">
              Check your CSV file and try again.
            </span>
          </div>
        </div>
      )}

      {/* Upload action */}
      {file && !isUploading && status !== "success" && (
        <div className="upload-actions">
          <button
            className="upload-submit-btn"
            type="button"
            onClick={uploadFile}
            disabled={isUploading}
          >
            <span>1 File Ingestion and Parsing </span>
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M5 12h14" />
              <path d="m12 5 7 7-7 7" />
            </svg>
          </button>

          <span className="upload-action-hint">
            Ready to clean and profile your data
          </span>
        </div>
      )}
    </section>
  );
}