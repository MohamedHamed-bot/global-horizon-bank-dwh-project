# 🚀 Deployment Guide: Global Horizon Bank Dashboard

Follow these steps to publish your Streamlit dashboard to the web using **Streamlit Cloud**.

## 1. Prerequisites
- Your project must be pushed to a **GitHub repository**.
- Ensure the following files are in your root directory:
  - `requirements.txt` (Python dependencies)
  - `packages.txt` (System dependencies for SQL drivers)
  - `data/` (Your raw CSV files if you want CSV fallback to work)
  - `dashboard/app.py` (The main application file)

## 2. Deploy to Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/).
2. Sign in with your GitHub account.
3. Click **"Create app"**.
4. Select your repository, branch (e.g., `main`), and set the **Main file path** to:
   `dashboard/app.py`
5. Click **"Deploy!"**.

## 3. (Optional) Connecting to SQL Server
If you want the dashboard to connect to a live SQL Server instead of using CSV files:
1. In your Streamlit Cloud dashboard, go to **Settings** > **Secrets**.
2. Add your database credentials:
   ```toml
   SQLSERVER_HOST = "your-database-host"
   SQLSERVER_PORT = "1433"
   SQLSERVER_USER = "your-username"
   SQLSERVER_PASSWORD = "your-password"
   SQLSERVER_DB = "GlobalHorizon_DWH"
   ```
3. The app will automatically detect these secrets and attempt to connect to SQL first.

## 4. Troubleshooting common issues
- **ModuleNotFoundError**: Ensure all libraries used in `app.py` are listed in `requirements.txt`.
- **FileNotFoundError**: Ensure the data folder is included in your GitHub repo. The app uses relative paths (`../data/raw/`) from the `dashboard/` folder.
- **SQL Driver Error**: `packages.txt` must contain `freetds-dev` for `pymssql` to work on Linux environments like Streamlit Cloud.

---
**Note:** The current version of `app.py` includes a **Demo Mode** fallback, so even if your data files are missing or the database is down, the dashboard will still show synthetic data for demonstration purposes!

## 🔗 Final Result
Your dashboard is live at: [**https://global-horizon-bank-dwh-project.streamlit.app/**](https://global-horizon-bank-dwh-project.streamlit.app/)
