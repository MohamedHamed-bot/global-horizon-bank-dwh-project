<div align="center">
  <img src="https://img.icons8.com/color/96/000000/bank-building.png" alt="Bank Logo" width="80" height="80">

  # Global Horizon Bank - Enterprise Data Warehouse

  **End-to-End Banking Data Intelligence Architecture**

  [![Python](https://img.shields.io/badge/Python-3.11+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org)
  [![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg?style=for-the-badge&logo=streamlit)](https://streamlit.io/)
  [![Pandas](https://img.shields.io/badge/Pandas-Analytics-150458.svg?style=for-the-badge&logo=pandas)](https://pandas.pydata.org/)
  [![Plotly](https://img.shields.io/badge/Plotly-Visuals-3F4F75.svg?style=for-the-badge&logo=plotly)](https://plotly.com/)

  <p align="center">
    <b>Transforming transactional data into high-impact business decisions for the Egyptian market.</b>
  </p>

  [**🚀 View Live Dashboard**](https://global-horizon-bank-dwh-project.streamlit.app/)
</div>

---

## 🏗️ Modern Architecture Pipeline
![Data Pipeline](diagrams/data_pipeline.png)

---

## 📊 Analytics & Insights Dashboard
The **Global Horizon Bank Dashboard** is a state-of-the-art analytical tool designed for executive decision-making.

### Key Features:
- **Executive KPIs**: Real-time monitoring of Transactions, Volume, Average Ticket, Active Accounts, and Weekend Share with period-over-period deltas.
- **Localized Context**: Specifically tailored for the Egyptian banking sector, including **Governorate-level analysis** (Cairo, Giza, Alexandria, Dakahlia, etc.).
- **Loan Portfolio Analytics**: Dedicated module for tracking loan types, status distribution, and portfolio age.
- **Intelligent Recommendations**: A rule-based engine that identifies risks (branch concentration, momentum shifts) and premium growth opportunities.
- **Dynamic Controls**: Switch between **Volume ($)** and **Transaction Count**, adjust time grains (**Year/Quarter/Month**), and filter by demographics.

---

## 🗂️ Data Models
### OLTP System (Transactional)
Designed for high-integrity daily operations.
![OLTP ERD](diagrams/oltp_erd_v2.png)

### OLAP Data Warehouse (Analytical)
Optimized Star Schema for high-performance complex queries.
![OLAP ERD](diagrams/olap_erd_v2.png)

---

## 🛠️ How to Run Locally

1. **Prerequisites**: Ensure you have Python 3.11+ installed.
2. **Installation**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Data Preparation**: (Optional) Re-generate the synthetic Egypt-market data.
   ```bash
   python src/data_generation.py
   ```
4. **Execution**:
   ```bash
   streamlit run dashboard/app.py
   ```
5. **Access**: Open your browser at `http://localhost:8501`.

---

## ☁️ Deployment Guide

### Streamlit Cloud (Recommended)
1. Push this repository to your **GitHub**.
2. Visit [Streamlit Cloud](https://share.streamlit.io/) and connect your account.
3. Select this repository and the `dashboard/app.py` as the main file.
4. **Secrets Management**: If using the SQL Server fallback, add your credentials (HOST, USER, PASS, etc.) to the Streamlit Cloud "Secrets" panel.
5. **Auto-Loading**: The app is configured to automatically detect and load the CSV files bundled in the repository, making it plug-and-play.

### Docker Deployment
```bash
docker-compose up --build
```

---

<div align="center">
  <i>Developed by Antigravity AI for the Data Engineering Diploma</i>
</div>
