# Streamlit Analytics Dashboard Guide

This document outlines the design and functionality of the executive reporting dashboard built for Phase 9 of the project.

## 1. Overview
The dashboard (`dashboard/app.py`) is designed as the presentation layer of the Data Warehouse. It allows business analysts and executives to consume the dimensional data visually without writing SQL. It is built using Python, `Streamlit` (for the web framework), and `Plotly Express` (for interactive charting).

## 2. Architecture & Data Ingestion
The dashboard reads directly from the SQL Server Data Warehouse (`GlobalHorizon_DWH`) using a cached `pymssql` connection.  
The `load_data()` query joins the fact table with Date, Branch, Customer, and Account dimensions to produce an analysis-ready dataframe for slicing and charting.

### Production Data Policy
- In production mode (`STREAMLIT_ENV=production` with `REQUIRE_SQL_IN_PRODUCTION=true`), SQL connectivity is mandatory.
- If SQL is unavailable in production, the app stops with a clear configuration error instead of silently switching to demo data.
- Demo fallback is preserved only for non-production/development execution.

### Consumption Pattern
The app follows a semantic-consumption pattern:
- Query dimensional model once into memory (cached for 10 minutes)
- Apply interactive filters in Streamlit sidebar
- Recompute KPIs, trends, and recommendations based on the filtered slice

## 3. Key Performance Indicators (KPIs)
The KPI section exposes five executive metrics with period-over-period context:
- **Total Transactions**: Measures overall system load.
- **Total Volume ($)**: Measures the absolute financial flow through the bank.
- **Average Ticket ($)**: Captures transaction quality/value intensity.
- **Active Accounts Transacting**: Derived engagement metric.
- **Weekend Share (%)**: Indicates non-weekday behavioral concentration.

Each KPI includes a delta against a matched previous window to highlight directional change.

## 4. Interactivity Controls
The sidebar contains two layers:

### Data Filters
- Date range
- Transaction type
- Branch and branch state
- Age group
- Account type and account status
- Amount range

### Analysis Controls
- **Metric Mode**: switch all key aggregations between `Amount` and `Transaction Count`
- **Trend Time Grain**: `Day`, `Week`, `Month`, or `Quarter`
- **Top N Branches**: configurable ranking scope for branch performance visuals

## 5. Dashboard Tabs & Visualizations

### Overview
- Transaction mix by type (pie)
- Configurable temporal trend line
- Top-N branch ranking
- Age-group demographic performance

### Behavior Analysis
- Branch x transaction type heatmap
- Transaction value distribution (box plot)
- Account-type performance
- State-level treemap
- Time-grain activity timeline

### Business Recommendations
Rule-based recommendation cards are generated from the current filtered context and prioritized by severity (`High`, `Medium`, `Low`).

### Data Explorer
Sortable filtered records with CSV download for ad-hoc analysis and offline sharing.

## 6. Business Recommendations Framework
Recommendations are transparent and deterministic (non-ML), including:
- **Concentration Risk**: flags when one branch dominates selected activity
- **Weekend Intensity**: prompts staffing/liquidity adjustment when weekend share is high
- **Momentum Shift**: compares current and previous periods to detect decline/growth
- **High-Value Opportunity**: surfaces premium-product opportunity when average ticket is above baseline
- **Transaction Mix Imbalance**: suggests diversification when one type dominates

This layer turns dashboard monitoring into actionable guidance for operations, growth, and customer strategy.

## 7. Data Coverage Notes
- Generated transaction history now includes data through **2026**.
- The demo dataset used for development fallback also includes 2026 dates to keep behavior consistent across environments.
