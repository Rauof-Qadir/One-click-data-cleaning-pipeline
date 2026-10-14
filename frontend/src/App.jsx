import { useRef, useState, useEffect } from "react";
import Navbar from "./components/Navbar";
import UploadCard from "./components/UploadCard";
import QualityScoreCard from "./components/QualityScoreCard";
import ColumnAnalysisList from "./components/ColumnAnalysisList";
import TrimColumnsStep from "./components/TrimColumnsStep";
import Text_and_String_cleaning4 from "./components/Text_and_String_cleaning4";
import Datatype_and_Formatconversion5 from "./components/Datatype_and_Formateconversion5";
import MissingValueImputationStep from "./components/MissingValueImputationStep";
import DuplicateResolutionStep from "./components/DuplicateResolutionStep";
import NumericValidationStep from "./components/NumericValidationStep";
import CategoricalStandardizationStep from "./components/CategoricalStandardizationStep";
import TemporalValidationStep from "./components/TemporalValidationStep";
import DomainValidationStep from "./components/DomainValidationStep";
import CrossColumnConsistencyStep from "./components/CrossColumnConsistencyStep";
import AnomalyDetectionStep from "./components/AnomalyDetectionStep";
import FinalQAVerificationStep from "./components/FinalQAVerificationStep";
import ReportingExportStep from "./components/ReportingExportStep";

import "./App.css";

const API_URL = "http://localhost:8000/api/upload";
const COUNTS_API_URL = "http://localhost:8000/api/transform/record-counts";

const PROCESSING_STEPS = [
  "Detecting file compression...",
  "Validating CSV structure...",
  "Detecting file encoding...",
  "Analyzing delimiters...",
  "Checking quotes and line breaks...",
  "Cleaning and standardizing headers...",
  "Scanning for malformed rows...",
  "Checking BOM and line endings...",
  "Standardizing embedded newlines...",
  "Generating metadata...",
  "Finalizing your workspace...",
];

export default function App() {
  const inputRef = useRef(null);

  const [file, setFile] = useState(null);
  const [status, setStatus] = useState("idle");
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [countsData, setCountsData] = useState(null);
  const [isCounting, setIsCounting] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);

  const isUploading = status === "uploading";

  useEffect(() => {
    if (progress !== 100 || status !== "uploading") return;

    const interval = setInterval(() => {
      setStepIndex((previous) => (previous + 1) % PROCESSING_STEPS.length);
    }, 1500);

    return () => clearInterval(interval);
  }, [progress, status]);

  function selectFile(selectedFile) {
    if (!selectedFile) return;

    setError("");
    setResult(null);
    setCountsData(null);
    setProgress(0);
    setStepIndex(0);

    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      setFile(null);
      setStatus("error");
      setError("Please select a CSV file only.");

      if (inputRef.current) inputRef.current.value = "";
      return;
    }

    setFile(selectedFile);
    setStatus("idle");
  }

  function uploadFile() {
    if (!file || isUploading) return;

    setStatus("uploading");
    setProgress(0);
    setStepIndex(0);
    setResult(null);
    setCountsData(null);
    setError("");

    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.open("POST", API_URL);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) {
        setProgress(
          Math.round((event.loaded / event.total) * 100)
        );
      }
    };

    xhr.onload = () => {
      let data;

      try {
        data = JSON.parse(xhr.responseText);
      } catch {
        data = {};
      }

      if (xhr.status >= 200 && xhr.status < 300 && data.success) {
        setProgress(100);
        setResult(data);
        setStatus("success");
      } else {
        setStatus("error");
        setError(
          typeof data.detail === "string"
            ? data.detail
            : `Upload failed (${xhr.status}). Please try again.`
        );
      }
    };

    xhr.onerror = () => {
      setStatus("error");
      setError(
        "Cannot connect to the backend. Make sure FastAPI is running."
      );
    };

    xhr.onabort = () => {
      setStatus("error");
      setError("The upload was interrupted. Please try again.");
    };

    xhr.send(formData);
  }

  async function recordRowColumnCounts() {
    if (!result?.standardized_file_path || isCounting) return;

    setIsCounting(true);
    setError("");

    try {
      const response = await fetch(COUNTS_API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          file_path: result.standardized_file_path,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Failed to analyze the dataset."
        );
      }

      setCountsData(data.data);
    } catch (err) {
      setError(
        err.message || "Cannot connect to the Transformation API."
      );
    } finally {
      setIsCounting(false);
    }
  }

  function reset() {
    setFile(null);
    setResult(null);
    setError("");
    setProgress(0);
    setStepIndex(0);
    setStatus("idle");
    setCountsData(null);
    setIsCounting(false);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  return (
    <main className="app">
      <div className="ambient ambient-one" aria-hidden="true" />
      <div className="ambient ambient-two" aria-hidden="true" />

      <Navbar />

      <section className="hero">
        <div className="hero-content">
          <div className="eyebrow">
            <span className="eyebrow-sparkle">✦</span>
            YOUR DATA JOURNEY STARTS HERE
          </div>

          <h1 className="hero-title">
            Clean data.
            <br />
            <span>Clear decisions.</span>
          </h1>

          <p className="subtitle">
            Turn messy CSV files into trustworthy data.
            Upload your dataset, inspect its quality, and get
            ready for your next analytics pipeline.
          </p>

          <div className="hero-highlights">
            <span>
              <span className="highlight-check">✓</span>
              Smart CSV inspection
            </span>
            <span>
              <span className="highlight-check">✓</span>
              Column-level profiling
            </span>
            <span>
              <span className="highlight-check">✓</span>
              Quality insights
            </span>
          </div>
        </div>

        <UploadCard
          file={file}
          isUploading={isUploading}
          progress={progress}
          stepIndex={stepIndex}
          processingSteps={PROCESSING_STEPS}
          status={status}
          result={result}
          error={error}
          inputRef={inputRef}
          selectFile={selectFile}
          uploadFile={uploadFile}
          reset={reset}
        />

        {error && result?.standardized_file_path && (
          <div className="analysis-error" role="alert">
            <span>!</span>
            <p>{error}</p>
            <button
              type="button"
              onClick={() => setError("")}
              aria-label="Dismiss error"
            >
              ×
            </button>
          </div>
        )}

        {result?.standardized_file_path && (
          <section className="transformation-section">
            <div className="section-heading">
              <div className="section-icon">⌘</div>
              <div>
                <span className="section-kicker">
                  DATA INTELLIGENCE
                </span>
                <h2>Data analysis pipeline</h2>
                <p>
                  Explore your dataset structure and identify
                  potential data-quality issues.
                </p>
              </div>
            </div>

            {!countsData ? (
              <div className="analysis-launch-card">
                <div className="analysis-launch-icon">◈</div>
                <div className="analysis-launch-copy">
                  <strong>
                    Ready to inspect your dataset?
                  </strong>
                  <span>
                    Analyze column types, missing values,
                    distributions, and quality indicators.
                  </span>
                </div>

                <button
                  className="upload-btn analyze-btn"
                  onClick={recordRowColumnCounts}
                  disabled={isCounting}
                  type="button"
                >
                  {isCounting ? (
                    <>
                      <span className="button-spinner" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      2 Initial Data Profiling
                      <span>→</span>
                    </>
                  )}
                </button>
              </div>
            ) : (
              <div className="analysis-results">
                <div className="analysis-complete">
                  <div className="complete-icon">✓</div>
                  <div>
                    <strong>Analysis complete</strong>
                    <p>
                      Your dataset profile is ready to explore.
                    </p>
                  </div>
                  <span className="complete-status">
                    COMPLETED
                  </span>
                </div>

                <QualityScoreCard
                  qualityScore={countsData.quality_score}
                />

                <div className="stats summary-stats">
                  <div className="summary-stat">
                    <span className="summary-stat-icon">▤</span>
                    <div>
                      <span>Total rows</span>
                      <strong>
                        {countsData.rows?.toLocaleString() ?? "—"}
                      </strong>
                    </div>
                  </div>

                  <div className="summary-stat">
                    <span className="summary-stat-icon">▥</span>
                    <div>
                      <span>Total columns</span>
                      <strong>{countsData.columns ?? "—"}</strong>
                    </div>
                  </div>

                  <div className="summary-stat">
                    <span className="summary-stat-icon">⚿</span>
                    <div>
                      <span>Potential keys</span>
                      <strong>
                        {countsData.potential_keys?.length ?? 0}
                      </strong>
                    </div>
                  </div>

                  <div className="summary-stat">
                    <span className="summary-stat-icon">⧉</span>
                    <div>
                      <span>Duplicate rows</span>
                      <strong>
                        {countsData.duplicate_rows_count?.toLocaleString() ?? 0}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="column-analysis-heading">
                  <div>
                    <span className="section-kicker">
                      SCHEMA EXPLORER
                    </span>
                    <h3>Column intelligence</h3>
                  </div>

                  <span className="column-count">
                    {Object.keys(countsData.data_types || {}).length} columns
                  </span>
                </div>

                <ColumnAnalysisList countsData={countsData} />

                {/* Header Cleaning Step */}
                <TrimColumnsStep 
                  filePath={countsData?.file_path || result?.standardized_file_path} 
                  onProcessed={(newPath) => {
                    console.log("Processed Header File Path:", newPath);
                  }} 
                />

                {/* Advanced Text Standardization Step */}
                <Text_and_String_cleaning4 
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  onProcessed={(newPath) => {
                    console.log("Text Standardized File Path:", newPath);
                  }}
                />

                {/* Type Inference & Parsing Step */}
                <Datatype_and_Formatconversion5
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  onProcessed={(newPath) => {
                    console.log("Type Inferred File Path:", newPath);
                  }}
                />

                {/* Missing Value Analysis & Imputation Step */}
                <MissingValueImputationStep
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  onProcessed={(newPath) => {
                    console.log("Missing Imputed File Path:", newPath);
                  }}
                />

                {/* Duplicate Detection & Entity Resolution Step (Yahan par rakha gaya hai) */}
                <DuplicateResolutionStep
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  onProcessed={(newPath) => {
                    console.log("Duplicate Resolved File Path:", newPath);
                  }}
                />

                {/* Numeric Validation & Outlier Detection Step */}
                <NumericValidationStep
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  onProcessed={(newPath) => {
                    console.log("Numeric Validated File Path:", newPath);
                }}
              />

                {/* Categorical Standardization & Mapping Step */}
                <CategoricalStandardizationStep
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  onProcessed={(newPath) => {
                    console.log("Categorical Standardized File Path:", newPath);
              }}
              />

              {/* Temporal Validation & Date/Time Step */}
                <TemporalValidationStep
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  onProcessed={(newPath) => {
                    console.log("Temporal Validated File Path:", newPath);
                   }}
                    />

              {/* Domain Validation & Integrity Step */}
                <DomainValidationStep
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  onProcessed={(newPath) => {
                    console.log("Domain Validated File Path:", newPath);
                  }}
                   />

              {/* Cross-Column Consistency Step */}
                <CrossColumnConsistencyStep
                    filePath={countsData?.file_path || result?.standardized_file_path}
                    onProcessed={(newPath) => {
                      console.log("Cross-Column Consistent File Path:", newPath);
                 }}
                  />


                {/* Anomaly & Outlier Detection Step */}
                <AnomalyDetectionStep
                   filePath={countsData?.file_path || result?.standardized_file_path}
                   onProcessed={(newPath) => {
                   console.log("Anomaly Detected File Path:", newPath);
                     }}
                   />

                {/* Final QA, Verification & Compliance Step */}
                <FinalQAVerificationStep
                  filePath={countsData?.file_path || result?.standardized_file_path}
                  originalRows={countsData?.rows}
                  onProcessed={(newPath) => {
                  console.log("Final QA Verified File Path:", newPath);
                 }}
                    />

                  {/* Reporting, Export & Compliance Step */}
                    <ReportingExportStep
                       filePath={countsData?.file_path || result?.standardized_file_path}
                       onProcessed={(newPath) => {
                         console.log("Final Export File Path:", newPath);
                    }}
                       />

                <button
                  className="recheck-btn"
                  type="button"
                  onClick={recordRowColumnCounts}
                  disabled={isCounting}
                >
                  {isCounting ? "Refreshing..." : "Refresh analysis ↻"}
                </button>
              </div>
            )}
          </section>
        )}

        <div className="workflow-strip">
          <div className="workflow-step">
            <span>01</span>
            <div>
              <strong>Upload</strong>
              <p>Bring your CSV</p>
            </div>
          </div>
          <div className="workflow-connector" />
          <div className="workflow-step">
            <span>02</span>
            <div>
              <strong>Inspect</strong>
              <p>Understand your data</p>
            </div>
          </div>
          <div className="workflow-connector" />
          <div className="workflow-step">
            <span>03</span>
            <div>
              <strong>Improve</strong>
              <p>Make better decisions</p>
            </div>
          </div>
        </div>
      </section>

      <footer className="app-footer">
        <a className="footer-brand" href="/">
          DataClean <span>Studio</span>
        </a>
        <p>Built for cleaner data and smarter decisions.</p>
        <span className="footer-status">
          <span /> Your workspace, your workflow
        </span>
      </footer>
    </main>
  );
}