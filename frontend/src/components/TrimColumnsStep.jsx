
import { useState } from "react";
import "./styles/TrimColumnsStep.css";

const API_URL = "http://localhost:8000/api/transform/clean-headers";

function getColumnStatus(item) {
  if (item.is_fully_empty_column) {
    return { label: "Empty column", type: "danger", icon: "🚫" };
  }

  if (item.is_near_duplicate) {
    return { label: "Possible duplicate", type: "warning", icon: "🔤" };
  }

  if (item.is_spreadsheet_index) {
    return { label: "Index column", type: "purple", icon: "🔢" };
  }

  if (item.is_empty || item.is_unnamed) {
    return { label: "Unnamed column", type: "danger", icon: "⚠️" };
  }

  if (item.is_auto_generated) {
    return { label: "Auto-generated", type: "warning", icon: "🤖" };
  }

  if (item.has_multiple_values) {
    return { label: "Multiple values", type: "info", icon: "🔀" };
  }

  return { label: "Looks good", type: "success", icon: "✓" };
}

export default function TrimColumnsStep({ filePath, onProcessed }) {
  const [loading, setLoading] = useState(false);
  const [processedData, setProcessedData] = useState(null);
  const [style, setStyle] = useState("snake_case");
  const [error, setError] = useState("");

  const handleProcessHeaders = async () => {
    if (!filePath || loading) return;

    setLoading(true);
    setError("");

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          file_path: filePath,
          normalization_style: style,
        }),
      });

      let data;

      try {
        data = await response.json();
      } catch {
        throw new Error("The server returned an invalid response.");
      }

      if (!response.ok || !data.success) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Failed to process headers."
        );
      }

      if (!data.data) {
        throw new Error("The server response is missing processed data.");
      }

      setProcessedData(data.data);
      if (onProcessed) onProcessed(data.data.file_path);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Cannot connect to Header Transformation API."
      );
    } finally {
      setLoading(false);
    }
  };

  const columns = processedData?.column_flags ?? [];
  const nearDuplicates = processedData?.near_duplicate_pairs ?? [];
  const emptyRows = processedData?.empty_rows_indices ?? [];

  const flaggedColumns = columns.filter((item) => {
    const status = getColumnStatus(item);
    return status.type !== "success";
  }).length;

  return (
    <section className="trim-card">
      <div className="trim-card__header">
        <div className="trim-heading">
          <div className="trim-icon" aria-hidden="true">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M4 7h16M4 12h10M4 17h7" />
              <path d="m17 15 3 3-3 3" />
              <path d="M20 18h-5" />
            </svg>
          </div>

          <div>
            <span className="trim-kicker">TRANSFORMATION · STEP 01</span>
            <h3>Advanced header cleaning</h3>
            <p>
              Standardize column names and identify potential structural
              issues before cleaning your data.
            </p>
          </div>
        </div>

        <span
          className={`trim-status ${
            processedData ? "trim-status--complete" : ""
          }`}
        >
          <span className="trim-status__dot" />
          {processedData ? "Completed" : "Ready to run"}
        </span>
      </div>

      {!processedData ? (
        <div className="trim-setup">
          <div className="trim-feature-grid">
            <div className="trim-feature">
              <span>✂</span>
              <div>
                <strong>Clean names</strong>
                <small>Trim spaces and symbols</small>
              </div>
            </div>

            <div className="trim-feature">
              <span>⇄</span>
              <div>
                <strong>Normalize format</strong>
                <small>Consistent naming style</small>
              </div>
            </div>

            <div className="trim-feature">
              <span>⌕</span>
              <div>
                <strong>Detect issues</strong>
                <small>Empty, duplicate and index names</small>
              </div>
            </div>

            <div className="trim-feature">
              <span>✓</span>
              <div>
                <strong>Inspect structure</strong>
                <small>Review detected column flags</small>
              </div>
            </div>
          </div>

          <div className="trim-controls">
            <label className="trim-select-field">
              <span>Column naming convention</span>
              <select
                value={style}
                onChange={(event) => setStyle(event.target.value)}
                disabled={loading}
              >
                <option value="snake_case">snake_case</option>
                <option value="lowercase">lowercase</option>
                <option value="uppercase">UPPERCASE</option>
              </select>
            </label>

            <button
              className="trim-run-button"
              onClick={handleProcessHeaders}
              disabled={loading || !filePath}
              type="button"
            >
              {loading ? (
                <>
                  <span className="trim-spinner" />
                  Processing headers...
                </>
              ) : (
                <>
                  3 Table Structure and Header
                  <span aria-hidden="true">→</span>
                </>
              )}
            </button>
          </div>

          {!filePath && (
            <p className="trim-hint">
              Upload a CSV and complete the previous step to continue.
            </p>
          )}

          {loading && (
            <div className="trim-loading-track" aria-label="Processing">
              <span />
            </div>
          )}
        </div>
      ) : (
        <div className="trim-results">
          <div className="trim-success-banner">
            <div className="trim-success-check">✓</div>
            <div>
              <strong>Header pipeline completed</strong>
              <p>
                Naming convention applied: <code>{style}</code>
              </p>
            </div>
            <span className="trim-success-tag">SUCCESS</span>
          </div>

          <div className="trim-metrics">
            <div className="trim-metric">
              <span className="trim-metric__label">Columns inspected</span>
              <strong>{columns.length.toLocaleString()}</strong>
            </div>
            <div className="trim-metric">
              <span className="trim-metric__label">Flagged columns</span>
              <strong>{flaggedColumns.toLocaleString()}</strong>
            </div>
            <div className="trim-metric">
              <span className="trim-metric__label">Possible name matches</span>
              <strong>{nearDuplicates.length.toLocaleString()}</strong>
            </div>
            <div className="trim-metric">
              <span className="trim-metric__label">Empty row positions</span>
              <strong>{emptyRows.length.toLocaleString()}</strong>
            </div>
          </div>

          {nearDuplicates.length > 0 && (
            <div className="trim-alert trim-alert--warning">
              <span className="trim-alert__icon">🔤</span>
              <div>
                <strong>Review similar column names</strong>
                <p>
                  These pairs may be typos or near-duplicates. Review them
                  before merging or renaming anything.
                </p>
                <div className="trim-pair-list">
                  {nearDuplicates.map((pair, index) => (
                    <span className="trim-pair" key={`${pair[0]}-${pair[1]}-${index}`}>
                      {pair[0]} <span>↔</span> {pair[1]}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {emptyRows.length > 0 && (
            <div className="trim-alert trim-alert--danger">
              <span className="trim-alert__icon">!</span>
              <div>
                <strong>Fully empty rows detected</strong>
                <p>
                  Reported row positions:{" "}
                  {emptyRows.slice(0, 30).join(", ")}
                  {emptyRows.length > 30 ? " …" : ""}
                </p>
              </div>
            </div>
          )}

          <div className="trim-columns-section">
            <div className="trim-section-heading">
              <div>
                <h4>Column inspection</h4>
                <p>Review each column's detected status.</p>
              </div>
              <span>{columns.length} columns</span>
            </div>

            {columns.length > 0 ? (
              <div className="trim-column-list">
                {columns.map((item, index) => {
                  const status = getColumnStatus(item);

                  return (
                    <div
                      className="trim-column-row"
                      key={`${item.column ?? "column"}-${index}`}
                      style={{ "--column-index": index }}
                    >
                      <div className="trim-column-number">
                        {String(index + 1).padStart(2, "0")}
                      </div>

                      <div className="trim-column-name">
                        <code>{item.column ?? "Unnamed column"}</code>
                      </div>

                      <span
                        className={`trim-column-badge trim-column-badge--${status.type}`}
                        title={status.label}
                      >
                        <span>{status.icon}</span>
                        {status.label}
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="trim-empty-state">
                The pipeline returned no column flags to display.
              </p>
            )}
          </div>

          <button
            className="trim-rerun-button"
            type="button"
            onClick={() => {
              setProcessedData(null);
              setError("");
            }}
          >
            ↻ Run again with different settings
          </button>
        </div>
      )}

      {error && (
        <div className="trim-error" role="alert">
          <span>!</span>
          <p>{error}</p>
          <button type="button" onClick={() => setError("")} aria-label="Dismiss error">
            ×
          </button>
        </div>
      )}
    </section>
  );
}
