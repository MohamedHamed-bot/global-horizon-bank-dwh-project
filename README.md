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

```mermaid
erDiagram
    BRANCHES ||--o{ EMPLOYEES : "manages"
    BRANCHES ||--o{ ACCOUNTS : "hosts"
    BRANCHES ||--o{ LOANS : "issues"
    CUSTOMERS ||--o{ ACCOUNTS : "owns"
    CUSTOMERS ||--o{ LOANS : "takes"
    ACCOUNTS ||--o{ TRANSACTIONS : "records"

    BRANCHES {
        int BranchID PK
        string BranchName
        string Address
        string City
        string State
        string ZipCode
    }

    EMPLOYEES {
        int EmployeeID PK
        string FirstName
        string LastName
        string Role
        int BranchID FK
        date HireDate
    }

    CUSTOMERS {
        int CustomerID PK
        string FirstName
        string LastName
        string Email
        string Phone
        string Address
        string City
        string State
        string ZipCode
        date DateOfBirth
        date JoinDate
    }

    ACCOUNTS {
        int AccountID PK
        int CustomerID FK
        int BranchID FK
        string AccountType
        float Balance
        date OpenDate
        string Status
    }

    LOANS {
        int LoanID PK
        int CustomerID FK
        int BranchID FK
        string LoanType
        float PrincipalAmount
        float InterestRate
        int TermMonths
        date StartDate
        string Status
    }

    TRANSACTIONS {
        int TransactionID PK
        int AccountID FK
        string TransactionType
        float Amount
        datetime TransactionDate
        string Description
        int RelatedAccountID FK
    }
```

### OLAP Data Warehouse (Analytical)
Optimized Star Schema for high-performance complex queries.

```mermaid
erDiagram
    FACT_TRANSACTION }|--|| DIM_DATE : "at"
    FACT_TRANSACTION }|--|| DIM_CUSTOMER : "by"
    FACT_TRANSACTION }|--|| DIM_BRANCH : "from"
    FACT_TRANSACTION }|--|| DIM_ACCOUNT : "on"

    FACT_TRANSACTION {
        int TransactionKey PK
        int TransactionID
        int DateKey FK
        int CustomerKey FK
        int AccountKey FK
        int BranchKey FK
        string TransactionType
        float Amount
    }

    DIM_CUSTOMER {
        int CustomerKey PK
        int CustomerID
        string FirstName
        string LastName
        string AgeGroup
        string City
        string State
        date EffectiveDate
        date ExpirationDate
        boolean IsCurrent
    }

    DIM_DATE {
        int DateKey PK
        date FullDate
        int Year
        int Quarter
        int Month
        int DayOfMonth
        string DayOfWeek
    }

    DIM_BRANCH {
        int BranchKey PK
        int BranchID
        string BranchName
        string City
        string State
        string ZipCode
    }

    DIM_ACCOUNT {
        int AccountKey PK
        int AccountID
        string AccountType
        date OpenDate
        string Status
    }
```

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
