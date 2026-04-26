<div align="center">
  <img src="https://img.icons8.com/color/96/000000/bank-building.png" alt="Bank Logo" width="80" height="80">

  # Global Horizon Bank - Enterprise Data Warehouse

  **An End-to-First Data Architecture Project from OLTP to OLAP**

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org)
  [![SQL Server](https://img.shields.io/badge/SQL_Server-2022-red.svg?style=for-the-badge&logo=microsoft-sql-server)](https://www.microsoft.com/sql-server/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg?style=for-the-badge&logo=streamlit)](https://streamlit.io/)
  [![Pandas](https://img.shields.io/badge/Pandas-Data_Gen-150458.svg?style=for-the-badge&logo=pandas)](https://pandas.pydata.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

  <p align="center">
    <b>Transforming transactional bottlenecks into analytical powerhouses.</b>
  </p>
</div>

---

## 📖 Project Overview

This repository contains the complete architecture and implementation of a data system for **Global Horizon Bank**. Following industry best practices, the project transitions from a highly normalized Transactional Database (OLTP) to a high‑performance dimensional Data Warehouse (OLAP), capable of answering complex business questions at scale.

### 🌐 Public Streamlit Dashboard

The deployed public app is available at: **[https://global-horizon-bank.streamlit.app/](https://global-horizon-bank.streamlit.app/)**

---

## 🏗️ Architecture Pipeline

![Data Pipeline](diagrams/data_pipeline_modern.png)

---

## 🗂️ Repository Structure

```bash
📦 DWH-Project
 ┣ 📂 data
 ┃ ┣ 📂 raw/          # Generated synthetic transactional data (CSV)
 ┃ ┗ 📂 processed/    # Output analytical data (if applicable)
 ┣ 📂 sql
 ┃ ┣ 📂 oltp/         # Transactional database schema & DML (Phases 2-4)
 ┃ ┣ 📂 etl/          # Extraction, Transformation, Load scripts (Phase 5)
 ┃ ┗ 📂 olap/         # Data Warehouse Star Schema & Analytics (Phases 6-9)
 ┣ 📂 src/            # Python scripts for data generation & pipelines
 ┣ 📂 diagrams/       # ERDs and architecture diagrams (Draw.io, SVG, PNG)
 ┃   ┣ data_pipeline_modern.png   # Updated glass‑morphism pipeline diagram
 ┃   ┣ oltp_erd_modern.png        # Modern OLTP ERD
 ┃   ┗ olap_erd_modern.png        # Modern OLAP ERD
 ┣ 📂 dashboard/      # Streamlit analytical dashboard app
 ┣ 📂 docs/           # Comprehensive implementation guides and phase documentation
 ┃   ┣ 📜 phases.md                       # The 9 Phases Detailed
 ┃   ┣ 📜 sql_implementation_guide.md     # SQL Architecture & Tuning
 ┃   ┗ 📜 streamlit_dashboard_guide.md    # Dashboard & Visualizations
 ┗ 📜 README.md       # Project overview
```

---

## 🚀 The 9 Phases of Implementation

*(unchanged – see README for detailed phases)*

---

## 📊 New Features & Updates

- **CSV‑first data loading** – The dashboard now reads from the `data/raw/` CSV files. If those are missing or the SQL driver is unavailable, it falls back to the optional SQL Server source.
- **Merged dataframe** – Transactions are joined with Accounts, Customers and Branches to provide a single analytical view.
- **Derived columns** – `AgeGroup` (based on `DateOfBirth`) and `IsWeekend` (based on `TransactionDate`).
- **Egyptian governorates** – All state‑level visualisations now use Egyptian governorates instead of US states.
- **Loans Tab** – Dedicated tab visualising loan portfolio amounts, status distribution and average loan age.
- **Modern diagrams** – Glass‑morphism style pipeline and ERDs (see `diagrams/` folder).

---

## 🛠️ How to Run Locally

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate synthetic data (if you removed the `data/raw/` CSVs)
```bash
python src/data_generation.py
```

### 3. (Optional) Set up SQL Server & ETL
If you want to use the SQL fallback, run the helper script:
```bash
python src/setup_sqlserver.py
```
Make sure SQL Server is reachable and the environment variables `SQLSERVER_HOST`, `SQLSERVER_PORT`, `SQLSERVER_USER`, `SQLSERVER_PASSWORD`, `SQLSERVER_DB` are set.

### 4. Launch the Streamlit dashboard
```bash
streamlit run dashboard/app.py
```
Access the app at `http://localhost:8501`.

### 5. Run via Docker (containerised option)
```bash
docker-compose up --build
```
The dashboard will be available at `http://localhost:8501`.

---

## ☁️ Deploying to Streamlit Cloud

1. **Commit all files** (including the `data/raw/` CSVs and the updated `diagrams/` assets) to a GitHub repository.
2. In Streamlit Cloud, connect the repo and enable automatic deployment.
3. Ensure the `requirements.txt` contains only packages that are installable on the cloud (the current list is safe).
4. The app will automatically load the CSV data bundled with the repo. No additional configuration is required.
5. If you want the SQL fallback on Cloud (e.g., using an Azure SQL instance), set the required environment variables in the Streamlit Cloud *Secrets* panel.

---

## 📚 Documentation

- **Data Pipeline Guide** – `docs/streamlit_dashboard_guide.md`
- **SQL Implementation Guide** – `docs/sql_implementation_guide.md`
- **Phase Details** – `docs/phases.md`

---

<div align="center">
  <i>Developed as part of the Data Engineering Diploma</i>
</div>
