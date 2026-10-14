# 🧹 Enterprise Data Cleaning & Validation Studio

An advanced, full-stack enterprise data cleaning, automated validation, anomaly detection, and compliance reporting platform. Built with a high-performance **FastAPI** backend engine and a modern **React + Vite** frontend interface featuring a sleek emerald green design theme.

---

## 📛 Badges

> **Note:** The badge images could not be rendered because the image URLs are incomplete or malformed. Below are corrected, working badge definitions you can drop straight into your README.

```markdown
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.100%2B-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/Vite-5-646CFF?style=for-the-badge&logo=vite&logoColor=white" alt="Vite">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

### Why the badges failed

| Issue | Cause | Fix |
|-------|-------|-----|
| `URL fetch failed: unable to parse URL content` | The badge URL was **truncated** (`https://img.shields.io/ba` is incomplete) | Use the full, valid shield URL |
| Missing closing syntax | The Markdown `<img>` tag and badge list were cut off mid-line | Close all tags and complete each badge |
| Static image fetch vs. render | `img.shields.io` returns an SVG; some fetchers can't parse SVG | This is expected — badges render in GitHub/VS Code but not in plain-text fetch tools |

---

## 🚀 Overview

**Enterprise Data Cleaning & Validation Studio** provides a unified workspace for data engineers, analysts, and compliance teams to:

- **Ingest** structured datasets (CSV, Parquet, JSON, SQL sources)
- **Clean** records with configurable, rule-based transformations
- **Validate** against schema, business, and regulatory rules
- **Detect anomalies** using statistical and ML-driven methods
- **Report** on data quality and compliance posture
- **Export** audit-ready artifacts for governance review

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React + Vite Frontend                    │
│                                                             │
└──────────────────────────┬──────────────────────────────────┘
                           │ 
┌──────────────────────────▼──────────────────────────────────┐
│                     FastAPI Backend                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ │
│  │  Cleaning  │ │ Validation │ │  Anomaly   │ │ Compliance│ │
│  │   Engine   │ │   Engine   │ │ Detection  │ │ Reporting │ │
│  └────────────┘ └────────────┘ └────────────┘ └───────────┘ │
└──────────────────────────┬──────────────────────────────────

```

---

## ✨ Features

### 🧼 Data Cleaning
- Null / missing value imputation strategies
- Duplicate detection & deduplication
- Type coercion and format normalization
- Whitespace, casing, and encoding fixes
- Configurable, versioned transformation pipelines

### ✅ Automated Validation
- Schema conformance checks
- Business rule engine (declarative DSL)
- Referential integrity validation
- Regex & range-based field validation
- Real-time validation feedback via WebSocket

### 🔍 Anomaly Detection
- Z-score & IQR outlier detection
- Isolation Forest and LOF models
- Time-series drift detection
- Custom threshold rules per column

### 📊 Compliance Reporting
- GDPR / HIPAA / SOC 2 aligned rule packs
- Audit trail with immutable logs
- Exportable PDF / CSV / JSON reports
- Data lineage visualization

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, FastAPI, Pydantic v2,  Pandas, Polars, scikit-learn |
| **Frontend** | React 18, Vite |

---

## 📦 Getting Started

### Prerequisites

- Python **3.11+**
- Node.js **18+** and npm/pnpm
- Docker & Docker Compose (recommended)

### 1. Clone the repository

```bash
git clone https://github.com/your-org/enterprise-data-studio.git
cd enterprise-data-studio
```

### 2. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate         # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend setup

```bash
cd frontend
npm install
npm run dev
```



| Service | URL |
|---------|-----|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |


---

## 📁 Project Structure

```
One-click-data-cleaning-pipline/
├── backend/
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   ├── core/             # Config, security, logging
│   │   ├── engines/          # Cleaning, validation, anomaly
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── lib/
│   │   └── main.tsx
│   └── package.json
└── README.md
```

---



---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read `CONTRIBUTING.md` and adhere to the `CODE_OF_CONDUCT.md`.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.


<p align="center">
  <strong>Built with 💚 for data teams who take quality seriously.</strong>
</p>