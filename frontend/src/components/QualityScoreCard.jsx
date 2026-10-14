import "./styles/QualityScoreCard.css";

export default function QualityScoreCard({ qualityScore }) {
  if (!qualityScore) return null;

  const overallScore = Number(qualityScore.overall_score ?? 0);
  const safeScore = Math.min(100, Math.max(0, overallScore));

  const scoreLevel =
    overallScore >= 80
      ? "excellent"
      : overallScore >= 50
        ? "moderate"
        : "critical";

  const scoreLabel =
    scoreLevel === "excellent"
      ? "Excellent"
      : scoreLevel === "moderate"
        ? "Needs improvement"
        : "Poor quality";

  const components = Object.entries(qualityScore.components || {});

  return (
    <section className={`quality-score-card quality-${scoreLevel}`}>
      <div className="quality-card-top">
        <div className="quality-title-group">
          <div className="quality-icon">
            <svg
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <path d="M12 3 4.5 6v5.5c0 4.7 3.2 7.8 7.5 9.5 4.3-1.7 7.5-4.8 7.5-9.5V6L12 3Z" />
              <path d="m8.5 12 2.3 2.3 4.8-5" />
            </svg>
          </div>

          <div>
            <h3>Data Quality Score</h3>
            <p>Your dataset's baseline quality assessment</p>
          </div>
        </div>

        <div className={`quality-status quality-status-${scoreLevel}`}>
          <span className="quality-status-dot" />
          {scoreLabel}
        </div>
      </div>

      <div className="quality-score-main">
        <div
          className="quality-score-ring"
          style={{ "--score-deg": `${safeScore * 3.6}deg` }}
          role="img"
          aria-label={`Overall data quality score: ${overallScore} out of 100`}
        >
          <div className="quality-score-ring-inner">
            <span className="quality-score-number">
              {Number.isFinite(overallScore) ? overallScore : 0}
            </span>
            <span className="quality-score-out-of">/ 100</span>
            <span className="quality-score-caption">Overall score</span>
          </div>
        </div>

        <div className="quality-score-insight">
          <span className="quality-insight-label">QUALITY OVERVIEW</span>

          <h4>
            {scoreLevel === "excellent" && "Looking good!"}
            {scoreLevel === "moderate" && "Room to improve"}
            {scoreLevel === "critical" && "Needs attention"}
          </h4>

          <p>
            {scoreLevel === "excellent" &&
              "Your dataset has a strong baseline quality score. Review individual metrics before starting your analysis."}

            {scoreLevel === "moderate" &&
              "Some quality issues may affect your analysis. Review the component scores to identify where improvements are needed."}

            {scoreLevel === "critical" &&
              "Your dataset may contain significant quality issues. Inspect the component scores before using it for analysis or modeling."}
          </p>

          <div className="quality-progress-track">
            <div
              className="quality-progress-fill"
              style={{ "--score-width": `${safeScore}%` }}
            />
          </div>

          <div className="quality-progress-labels">
            <span>0 — Poor</span>
            <span>100 — Excellent</span>
          </div>
        </div>
      </div>

      <div className="quality-components-heading">
        <div>
          <h4>Quality Breakdown</h4>
          <p>Explore the individual quality indicators</p>
        </div>

        <span className="quality-metric-count">
          {components.length}{" "}
          {components.length === 1 ? "metric" : "metrics"}
        </span>
      </div>

      {components.length > 0 ? (
        <div className="quality-components-grid">
          {components.map(([compName, compVal], index) => {
            const numericValue = Number(compVal);
            const hasNumericValue =
              compVal !== null &&
              compVal !== "" &&
              Number.isFinite(numericValue);

            const visualValue = hasNumericValue
              ? Math.min(100, Math.max(0, numericValue))
              : 0;

            return (
              <article
                className="quality-component"
                key={compName}
                style={{ "--metric-index": Math.min(index, 12) }}
              >
                <div className="quality-component-top">
                  <span
                    className="quality-component-marker"
                    aria-hidden="true"
                  >
                    {String(index + 1).padStart(2, "0")}
                  </span>

                  <span className="quality-component-name">
                    {compName.replace(/_/g, " ")}
                  </span>
                </div>

                <div className="quality-component-value">
                  <strong>{hasNumericValue ? numericValue : "—"}</strong>
                  <span>{hasNumericValue ? "%" : ""}</span>
                </div>

                <div className="quality-metric-track">
                  <div
                    className="quality-metric-fill"
                    style={{ "--metric-width": `${visualValue}%` }}
                  />
                </div>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="quality-no-components">
          <span className="quality-no-components-icon">i</span>
          <p>No individual quality metrics are available yet.</p>
        </div>
      )}

      <div className="quality-card-footer">
        <span className="quality-footer-icon" aria-hidden="true">✓</span>
        <span>
          Baseline assessment · Review individual metrics before cleaning
        </span>
      </div>
    </section>
  );
}