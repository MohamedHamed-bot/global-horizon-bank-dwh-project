# Streamlit Analytics Dashboard Guide

This document outlines the design and functionality of the executive reporting dashboard built for Phase 9 of the project.

## 1. Overview
The dashboard (`dashboard/app.py`) is designed as the presentation layer of the Data Warehouse. It allows business analysts and executives to consume the dimensional data visually without writing SQL. It is built using Python, `Streamlit` (for the web framework), and `Plotly Express` (for interactive charting).

## 2. Architecture & Data Ingestion
Since this project simulates an end-to-end flow locally, the dashboard utilizes the `pandas` library to ingest the generated CSV files from `data/raw/`. 
In a production environment, the `load_data()` function would be replaced with a `pyodbc` or `SQLAlchemy` connection string targeting the `GlobalHorizon_DWH` SQL Server database.

### The OLAP Simulation
Within the `load_data()` function, `pandas.merge()` is used to stitch the dimensional tables (`Customers`, `Branches`, `Accounts`) to the fact table (`Transactions`). This mimics the behavior of querying a Star Schema, resulting in a single flattened dataframe optimized for slicing.

## 3. Key Performance Indicators (KPIs)
The top section of the dashboard highlights four core business metrics:
- **Total Transactions**: Measures overall system load.
- **Total Volume ($)**: Measures the absolute financial flow through the bank.
- **Total Customers**: Measures the size of the user base.
- **Active Accounts Transacting**: A derived metric showing engagement (accounts that have initiated at least one transaction).

## 4. Visualizations (Plotly Express)

### Transaction Volume by Type (Pie Chart)
- **Insight**: Identifies the primary use case of the bank's accounts. If 'Withdrawals' heavily outweigh 'Deposits', it could signal a liquidity drain.

### Monthly Transaction Trend (Spline Line Chart)
- **Insight**: Tracks growth over time. The spline smoothing helps visualize the general trajectory, highlighting seasonal peaks (e.g., holiday spending) or valleys.

### Top Branches by Volume (Horizontal Bar Chart)
- **Insight**: Identifies high-performing geographic locations. This data informs where the bank should open new branches or close underperforming ones.

### Customer Demographics (Bar Chart)
- **Insight**: The ETL process creates an `AgeGroup` dimension. This chart visualizes that dimension, helping marketing teams understand the dominant demographic (e.g., Millennials vs. Retirees) for targeted product launches.

## 5. UI/UX Modernization
The dashboard utilizes custom CSS injected via `st.markdown(unsafe_allow_html=True)` to create "Metric Cards". This moves away from the default Streamlit styling, introducing a clean, white background with drop-shadows to mimic modern SaaS application designs.
