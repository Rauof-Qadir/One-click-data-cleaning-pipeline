import "./styles/ColumnAnalysisList.css";

export default function ColumnAnalysisList({ countsData }) {
  if (!countsData?.data_types) return null;

  const columns = Object.entries(countsData.data_types);

  const getTypeClass = (type) => {
    switch (type) {
      case "String/Text":
        return "type-text";
      case "Integer":
        return "type-integer";
      case "Float":
        return "type-float";
      case "Boolean":
        return "type-boolean";
      default:
        return "type-default";
    }
  };

  return (
    <section className="column-analysis">
      <div className="analysis-header">
        <div className="analysis-heading-group">
          <div className="analysis-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <rect x="3" y="3" width="18" height="18" rx="3" />
              <path d="M3 9h18M9 21V9" />
              <path d="M12 13h5M12 17h5" />
            </svg>
          </div>

          <div className="analysis-heading-text">
            <h3>Schema &amp; Quality Profile</h3>
            <p>Explore your dataset, one column at a time.</p>
          </div>
        </div>

        <div className="column-count-badge">
          <span className="column-count-dot" />
          {columns.length} {columns.length === 1 ? "Column" : "Columns"}
        </div>
      </div>

      <div className="analysis-summary">
        <div className="summary-item">
          <span className="summary-label">Total columns</span>
          <strong>{columns.length.toLocaleString()}</strong>
        </div>

        <div className="summary-divider" />

        <div className="summary-item">
          <span className="summary-label">With missing data</span>
          <strong>
            {
              columns.filter(([name]) => {
                return (
                  (countsData.column_stats?.[name]?.total_missing ?? 0) > 0
                );
              }).length
            }
          </strong>
        </div>

        <div className="summary-divider" />

        <div className="summary-item">
          <span className="summary-label">Potential keys</span>
          <strong>{countsData.potential_keys?.length ?? 0}</strong>
        </div>
      </div>

      <div className="column-list">
        {columns.map(([colName, typeName], index) => {
          const statsInfo = countsData.column_stats?.[colName];
          const hasMissing = (statsInfo?.total_missing ?? 0) > 0;
          const isConstant = statsInfo?.variance_status?.includes("Constant");
          const isEmptyColumn = statsInfo?.variance_status === "Empty";

          const numProfile = countsData.numeric_profiles?.[colName];
          const temporalProfile = countsData.temporal_profiles?.[colName];
          const anomalyInfo = countsData.anomaly_profiles?.[colName];

          const isKey = countsData.potential_keys?.some(
            (key) => key.column === colName
          );

          const isCategorical =
            typeName === "String/Text" || typeName === "Boolean";

          const topCats = statsInfo?.top_categories ?? [];

          return (
            <article
              className={`column-card ${
                isEmptyColumn ? "column-card-empty" : ""
              }`}
              key={colName}
              style={{ "--column-index": Math.min(index, 12) }}
            >
              <div className="column-card-header">
                <div className="column-identity">
                  <span className="column-index">
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <div className="column-name-wrap">
                    <h4 className="column-name" title={colName}>
                      {colName}
                    </h4>

                    <div className="column-tags">
                      {isKey && (
                        <span className="profile-tag tag-key">
                          <span aria-hidden="true">⌘</span> Potential key
                        </span>
                      )}

                      {isConstant && (
                        <span className="profile-tag tag-constant">
                          <span aria-hidden="true">❄</span>{" "}
                          {statsInfo.variance_status}
                        </span>
                      )}

                      {isEmptyColumn && (
                        <span className="profile-tag tag-empty">
                          Empty column
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="column-meta">
                  {statsInfo && !isEmptyColumn && (
                    <span className="unique-count" title="Distinct values">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        aria-hidden="true"
                      >
                        <circle cx="10.8" cy="10.8" r="6.8" />
                        <path d="m16 16 4.5 4.5" />
                      </svg>
                      {statsInfo.cardinality?.toLocaleString() ?? "—"} unique
                    </span>
                  )}

                  {hasMissing && !isEmptyColumn && (
                    <span
                      className="missing-badge"
                      title={`${statsInfo.blanks ?? 0} blank cells, ${
                        statsInfo.missing_tokens ?? 0
                      } placeholder tokens`}
                    >
                      <span className="missing-indicator" />
                      {statsInfo.total_missing.toLocaleString()} missing
                    </span>
                  )}

                  <span className={`data-type-badge ${getTypeClass(typeName)}`}>
                    {typeName}
                  </span>
                </div>
              </div>

              {numProfile && (
                <div className="profile-section">
                  <div className="profile-section-heading">
                    <span className="section-symbol numeric-symbol">∑</span>
                    <span>Numeric statistics</span>
                  </div>

                  <div className="numeric-grid">
                    {[
                      ["Minimum", numProfile.min],
                      ["Maximum", numProfile.max],
                      ["Mean", numProfile.mean],
                      ["Median", numProfile.median],
                      ["Std. deviation", numProfile.std_dev],
                    ].map(([label, value]) => (
                      <div className="numeric-stat" key={label}>
                        <span>{label}</span>
                        <strong title={String(value ?? "—")}>
                          {value ?? "—"}
                        </strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {temporalProfile && (
                <div className="profile-section">
                  <div className="profile-section-heading">
                    <span className="section-symbol temporal-symbol">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        aria-hidden="true"
                      >
                        <rect x="3" y="5" width="18" height="16" rx="2" />
                        <path d="M16 3v4M8 3v4M3 10h18" />
                      </svg>
                    </span>
                    <span>Temporal profile</span>
                  </div>

                  <div className="temporal-details">
                    <div className="temporal-range">
                      <span className="temporal-label">Date range</span>
                      <strong>
                        {temporalProfile.earliest ?? "—"}
                        <span className="range-arrow">→</span>
                        {temporalProfile.latest ?? "—"}
                      </strong>
                    </div>

                    <div className="temporal-duration">
                      <span className="temporal-label">Total span</span>
                      <strong>
                        {temporalProfile.total_span_days ?? "—"} days
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {anomalyInfo && anomalyInfo.outlier_count > 0 && (
                <div className="profile-section anomaly-section">
                  <div className="anomaly-banner">
                    <span className="anomaly-icon" aria-hidden="true">
                      !
                    </span>

                    <div className="anomaly-copy">
                      <strong>
                        {anomalyInfo.outlier_count.toLocaleString()} anomalies
                        detected
                      </strong>
                      <span>
                        {anomalyInfo.outlier_percentage}% of this column
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {isCategorical &&
                topCats.length > 0 &&
                !isEmptyColumn && (
                  <div className="profile-section categories-section">
                    <div className="profile-section-heading">
                      <span className="section-symbol category-symbol">
                        Aa
                      </span>
                      <span>Most frequent values</span>
                    </div>

                    <div className="category-list">
                      {topCats.map((cat, i) => (
                        <div
                          className="category-chip"
                          key={`${String(cat.value)}-${i}`}
                          title={`${cat.value}: ${cat.count} occurrences`}
                        >
                          <span className="category-value">{cat.value}</span>
                          <span className="category-count">
                            {Number(cat.count).toLocaleString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
            </article>
          );
        })}
      </div>

      {columns.length === 0 && (
        <div className="column-empty-state">
          <span className="empty-state-icon">∅</span>
          <h4>No columns found</h4>
          <p>Your dataset schema doesn't contain any columns yet.</p>
        </div>
      )}
    </section>
  );
}