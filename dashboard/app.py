# -*- coding: utf-8 -*-
"""Global Horizon Bank Dashboard

This Streamlit app loads the banking data warehouse either from CSV files (local
fallback) or from a SQL Server database. It builds a merged dataframe that
contains transactions, accounts, customers and branches. Additional derived
features – age groups, weekend flag and time‑grain columns – are calculated on
the fly. A dedicated **Loans** tab visualises loan portfolios.

The app is designed to run both locally (`streamlit run dashboard/app.py`) and
on Streamlit Cloud (the CSV files are bundled with the repo; the SQL connection
will be skipped when the driver is unavailable).
"""

import os
import random
from datetime import datetime
from typing import Tuple

import pandas as pd
import plotly.express as px
import streamlit as st

# Optional SQL driver – will be used only if available
try:
    import pymssql
    _PYMSSQL_AVAILABLE = True
except ImportError:
    _PYMSSQL_AVAILABLE = False

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Global Horizon Bank Dashboard",
    page_icon="🏦",
    layout="wide",
)

st.title("🏦 Global Horizon Bank Analytics")
st.markdown("### Data Warehouse Executive Dashboard")

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def _parse_date(col: pd.Series) -> pd.Series:
    """Parse a date column safely, returning a datetime dtype."""
    return pd.to_datetime(col, errors="coerce")

def derive_agegroup(dob: pd.Series) -> pd.Series:
    """Derive an age‑group label from a date‑of‑birth series.
    Groups: 18‑24, 25‑35, 36‑50, 51+ (based on today).
    """
    today = pd.Timestamp("today")
    age = (today - dob).dt.days // 365
    bins = [0, 24, 35, 50, 150]
    labels = ["18-24", "25-35", "36-50", "51+"]
    return pd.cut(age, bins=bins, labels=labels, right=False)

def is_weekend(date_series: pd.Series) -> pd.Series:
    """Return True for Saturday / Sunday values."""
    return date_series.dt.weekday.isin([5, 6])

def delta_label(current_value: float, previous_value: float, mode: str) -> str:
    if previous_value == 0:
        return "n/a vs previous"
    delta_pct = ((current_value - previous_value) / previous_value) * 100
    unit = "amount" if mode == "Sum" else "count"
    return f"{delta_pct:+.1f}% vs previous {unit}"

def generate_recommendations(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    full_df: pd.DataFrame,
    mode: str,
) -> list[dict]:
    recommendations = []
    
    current_sum = current_df["Amount"].sum() if not current_df.empty else 0.0
    previous_sum = previous_df["Amount"].sum() if not previous_df.empty else 0.0
    current_count = len(current_df)
    previous_count = len(previous_df)
    
    current_metric = current_sum if mode == "Sum" else float(current_count)
    previous_metric = previous_sum if mode == "Sum" else float(previous_count)

    global_avg_ticket = full_df["Amount"].mean() if not full_df.empty else 0.0
    current_avg_ticket = current_df["Amount"].mean() if not current_df.empty else 0.0

    if current_df.empty:
        return [{
            "severity": "Low",
            "title": "Insufficient data under current filters",
            "why": "The current selection has no transactions to evaluate.",
            "action": "Expand date, branch, or transaction filters to generate recommendations."
        }]

    weekend_share = float(current_df["IsWeekend"].mean() * 100)
    if weekend_share >= 40:
        recommendations.append({
            "severity": "High",
            "title": "Rebalance weekend staffing and liquidity windows",
            "why": f"Weekend activity is {weekend_share:.1f}% of selected transactions.",
            "action": "Increase weekend support coverage and adjust branch cash planning."
        })

    branch_metric = aggregate_by(current_df, "BranchName", mode, metric_label="Metric")
    if not branch_metric.empty and current_metric > 0:
        top_branch = branch_metric.sort_values("Metric", ascending=False).iloc[0]
        concentration = float((top_branch["Metric"] / current_metric) * 100)
        if concentration >= 35:
            recommendations.append({
                "severity": "High",
                "title": "Reduce branch concentration risk",
                "why": f"{top_branch['BranchName']} contributes {concentration:.1f}% of selected {mode.lower()} volume.",
                "action": "Transfer successful branch practices to nearby branches and monitor dependency."
            })

    if previous_metric > 0:
        trend_change = ((current_metric - previous_metric) / previous_metric) * 100
        if trend_change <= -10:
            recommendations.append({
                "severity": "High",
                "title": "Address declining momentum",
                "why": f"Selected period {mode.lower()} is down {abs(trend_change):.1f}% versus prior period.",
                "action": "Deploy retention campaigns for impacted customer/account segments."
            })
        elif trend_change >= 10:
            recommendations.append({
                "severity": "Medium",
                "title": "Scale capacity for growth areas",
                "why": f"Selected period {mode.lower()} is up {trend_change:.1f}% versus prior period.",
                "action": "Allocate service capacity to high-growth governorates and transaction types."
            })

    if current_avg_ticket > 0 and global_avg_ticket > 0 and current_avg_ticket >= (global_avg_ticket * 1.2):
        recommendations.append({
            "severity": "Medium",
            "title": "Launch premium offers for high-value segments",
            "why": f"Average ticket (${current_avg_ticket:,.2f}) exceeds global baseline (${global_avg_ticket:,.2f}).",
            "action": "Promote premium bundles and relationship-driven products for this segment."
        })

    tx_mix = aggregate_by(current_df, "TransactionType", "Count", metric_label="TxCount")
    if not tx_mix.empty and tx_mix["TxCount"].sum() > 0:
        tx_mix = tx_mix.sort_values("TxCount", ascending=False)
        top_tx = tx_mix.iloc[0]
        tx_share = float((top_tx["TxCount"] / tx_mix["TxCount"].sum()) * 100)
        if tx_share >= 50:
            recommendations.append({
                "severity": "Low",
                "title": "Diversify transaction mix",
                "why": f"{top_tx['TransactionType']} represents {tx_share:.1f}% of transaction count.",
                "action": "Bundle adjacent services to diversify customer transaction behavior."
            })

    if not recommendations:
        recommendations.append({
            "severity": "Low",
            "title": "Performance appears balanced",
            "why": "No major concentration or trend anomalies were detected for this slice.",
            "action": "Continue monitoring with branch and account-level drill-downs."
        })

    severity_order = {"High": 0, "Medium": 1, "Low": 2}
    recommendations.sort(key=lambda item: severity_order.get(item["severity"], 3))
    return recommendations

# ---------------------------------------------------------------------------
# Data loading – CSV with SQL fallback
# ---------------------------------------------------------------------------

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Load the core fact table and a backup demo dataframe.

    Returns:
        merged_df: The fully joined dataframe used throughout the app.
        demo_df:   A small synthetic dataframe used when CSV/SQL loading fails.
    """
    # Paths to raw CSV files (they live under the repository root)
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "raw"))
    tx_path = os.path.join(base_path, "transactions.csv")
    acc_path = os.path.join(base_path, "accounts.csv")
    cust_path = os.path.join(base_path, "customers.csv")
    branch_path = os.path.join(base_path, "branches.csv")
    loans_path = os.path.join(base_path, "loans.csv")

    # -------------------------------------------------------------------
    # Attempt CSV loading first
    # -------------------------------------------------------------------
    try:
        tx = pd.read_csv(tx_path)
        acc = pd.read_csv(acc_path)
        cust = pd.read_csv(cust_path)
        br = pd.read_csv(branch_path)
        loans = pd.read_csv(loans_path)
    except Exception as e:
        st.warning(f"CSV loading failed ({e}); attempting SQL fallback.")
        tx = acc = cust = br = loans = None

    # -------------------------------------------------------------------
    # If any CSV failed, try SQL (only when driver is present)
    # -------------------------------------------------------------------
    if any(df is None for df in [tx, acc, cust, br]):
        if not _PYMSSQL_AVAILABLE:
            st.error("Neither CSV files nor SQL driver are available. Showing demo data.")
            return demo_dataset()
        
        try:
            # Build connection string from env vars
            server = os.getenv("SQLSERVER_HOST", "localhost")
            port = int(os.getenv("SQLSERVER_PORT", "21433"))
            user = os.getenv("SQLSERVER_USER", "sa")
            password = os.getenv("SQLSERVER_PASSWORD", "YourStrong!Passw0rd")
            database = os.getenv("SQLSERVER_DB", "GlobalHorizonBankDW")
            
            conn = pymssql.connect(
                server=server,
                port=port,
                user=user,
                password=password,
                database=database,
                timeout=5  # Short timeout for cloud fallback
            )
            tx = pd.read_sql("SELECT * FROM dbo.Transactions", conn)
            acc = pd.read_sql("SELECT * FROM dbo.Accounts", conn)
            cust = pd.read_sql("SELECT * FROM dbo.Customers", conn)
            br = pd.read_sql("SELECT * FROM dbo.Branches", conn)
            loans = pd.read_sql("SELECT * FROM dbo.Loans", conn)
            conn.close()
        except Exception as sql_err:
            st.error(f"SQL Fallback failed ({sql_err}). Loading demo data.")
            return demo_dataset()

    # -------------------------------------------------------------------
    # Merge all tables – keep only the columns we need later
    # -------------------------------------------------------------------
    # Parse dates
    tx["TransactionDate"] = _parse_date(tx["TransactionDate"])
    acc["OpenDate"] = _parse_date(acc["OpenDate"])
    cust["DateOfBirth"] = _parse_date(cust["DateOfBirth"])
    loans["StartDate"] = _parse_date(loans["StartDate"])

    # Rename accounts Status -> AccountStatus before merge to avoid ambiguity
    acc = acc.rename(columns={"Status": "AccountStatus"})

    # Join transaction tables
    merged = (
        tx.merge(acc, on="AccountID", how="left")
        .merge(cust, on="CustomerID", how="left", suffixes=("", "_cust"))
        .merge(br, on="BranchID", how="left", suffixes=("", "_br"))
    )

    # Derive helper columns
    merged["Year"] = merged["TransactionDate"].dt.year
    merged["Quarter"] = merged["TransactionDate"].dt.quarter
    merged["MonthName"] = merged["TransactionDate"].dt.month_name()
    merged["BranchState"] = merged["State_br"]  # Egyptian governorate from branches table
    merged["AgeGroup"] = derive_agegroup(merged["DateOfBirth"])
    merged["IsWeekend"] = is_weekend(merged["TransactionDate"])

    # Pre-merge loans with branch info (so Loans tab doesn't need raw tables)
    loans_merged = loans.merge(br, on="BranchID", how="left", suffixes=("", "_br"))
    loans_merged["LoanAgeDays"] = (pd.Timestamp("today") - loans_merged["StartDate"]).dt.days

    return merged, loans_merged

# ---------------------------------------------------------------------------
# Demo dataset – used only when all loading steps fail
# ---------------------------------------------------------------------------

def demo_dataset() -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Create synthetic dataframes that mimic the real schema.
    This keeps the dashboard functional on environments where no data is
    available (e.g., Streamlit Cloud without the CSVs).
    """
    rows = 5000
    date_range = pd.date_range(start="2022-01-01", end="2026-12-31", freq="D")
    transaction_types = ["Deposit", "Withdrawal", "Transfer", "Payment"]
    branches = [
        ("Mansoura Branch", "Dakahlia"),
        ("Port Said Branch", "PortSaid"),
        ("Alexandria Branch", "Alexandria"),
        ("Cairo Branch", "Cairo"),
        ("Luxor Branch", "Luxor"),
    ]
    age_groups = ["18-24", "25-35", "36-50", "51+"]
    account_types = ["Savings", "Checking", "Business", "Credit"]
    account_statuses = ["Active", "Inactive", "Dormant"]
    loan_types = ["Personal", "Mortgage", "Auto", "Student"]
    loan_statuses = ["Active", "Paid", "Defaulted"]

    records = []
    for _ in range(rows):
        tx_date = random.choice(date_range)
        branch_name, branch_state = random.choice(branches)
        tx_type = random.choices(transaction_types, weights=[0.30, 0.28, 0.24, 0.18], k=1)[0]
        amount = round(random.expovariate(1 / 1500), 2)
        cust_id = random.randint(1, 10000)
        acct_id = random.randint(1, 12000)
        acct_type = random.choice(account_types)
        acct_status = random.choice(account_statuses)
        age_group = random.choice(age_groups)
        records.append(
            {
                "TransactionDate": tx_date,
                "TransactionType": tx_type,
                "Amount": amount,
                "BranchName": branch_name,
                "BranchState": branch_state,
                "CustomerID": cust_id,
                "AccountID": acct_id,
                "AccountType": acct_type,
                "AccountStatus": acct_status,
                "AgeGroup": age_group,
                "IsWeekend": tx_date.weekday() in (5, 6),
            }
        )
    df = pd.DataFrame.from_records(records)
    df["Year"] = df["TransactionDate"].dt.year
    df["Quarter"] = df["TransactionDate"].dt.quarter
    df["MonthName"] = df["TransactionDate"].dt.month_name()
    df["PeriodLabel"] = df["Year"].astype(str) # Default to Year label
    
    # Generate demo loans
    loan_records = []
    for _ in range(rows // 10):
        start_date = random.choice(date_range)
        loan_records.append({
            "LoanType": random.choice(loan_types),
            "PrincipalAmount": round(random.uniform(5000, 500000), 2),
            "Status": random.choice(loan_statuses),
            "StartDate": start_date,
            "LoanAgeDays": (pd.Timestamp("today") - start_date).days
        })
    loans_df = pd.DataFrame.from_records(loan_records)
    
    return df, loans_df

# ---------------------------------------------------------------------------
# Load data (merged transactions + loans)
# ---------------------------------------------------------------------------
merged_df, loans_df = load_data()
# The logic inside load_data already ensures these aren't empty via fallback
# but we can show a status message if we want.
if "PeriodLabel" not in merged_df.columns:
    # This might happen if fallback was used and we need to ensure basic columns exist
    merged_df["PeriodLabel"] = merged_df["Year"].astype(str)

# ---------------------------------------------------------------------------
# Sidebar – filters
# ---------------------------------------------------------------------------
st.sidebar.header("Filters")

# Date filter – use min/max from the dataframe
min_date = merged_df["TransactionDate"].min().date()
max_date = merged_df["TransactionDate"].max().date()
start_date, end_date = st.sidebar.date_input(
    "Transaction date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

# Transaction type filter
selected_types = st.sidebar.multiselect(
    "Transaction Types",
    options=merged_df["TransactionType"].unique().tolist(),
    default=merged_df["TransactionType"].unique().tolist(),
)

# Branch filter (by governorate)
selected_states = st.sidebar.multiselect(
    "Governorates",
    options=merged_df["BranchState"].unique().tolist(),
    default=merged_df["BranchState"].unique().tolist(),
)

# Age group filter
selected_age_groups = st.sidebar.multiselect(
    "Age Groups",
    options=merged_df["AgeGroup"].dropna().unique().tolist(),
    default=merged_df["AgeGroup"].dropna().unique().tolist(),
)

# Account type filter
selected_account_types = st.sidebar.multiselect(
    "Account Types",
    options=merged_df["AccountType"].unique().tolist(),
    default=merged_df["AccountType"].unique().tolist(),
)

# Amount range slider
min_amount = float(merged_df["Amount"].min())
max_amount = float(merged_df["Amount"].max())
selected_amount = st.sidebar.slider(
    "Transaction Amount (USD)",
    min_value=0.0,
    max_value=max_amount,
    value=(min_amount, max_amount),
)

# Metric mode (Sum vs Count)
metric_mode = st.sidebar.radio("Metric", ["Sum", "Count"], index=0)

# Time grain (Year / Quarter / Month)
time_grain = st.sidebar.selectbox("Time Grain", ["Year", "Quarter", "Month"]) 

# Top N for ranking visualisations
top_n = st.sidebar.slider("Top N", min_value=3, max_value=20, value=10)

# ---------------------------------------------------------------------------
# Apply filters to the merged dataframe
# ---------------------------------------------------------------------------
mask = (
    (merged_df["TransactionDate"] >= pd.Timestamp(start_date))
    & (merged_df["TransactionDate"] <= pd.Timestamp(end_date))
    & merged_df["TransactionType"].isin(selected_types)
    & merged_df["BranchState"].isin(selected_states)
    & merged_df["AgeGroup"].isin(selected_age_groups)
    & merged_df["AccountType"].isin(selected_account_types)
    & (merged_df["Amount"] >= selected_amount[0])
    & (merged_df["Amount"] <= selected_amount[1])
)
filtered_df = merged_df[mask]

# Calculate previous period for deltas
period_days = max((end_date - start_date).days + 1, 1)
previous_end_date = pd.Timestamp(start_date) - pd.Timedelta(days=1)
previous_start_date = previous_end_date - pd.Timedelta(days=period_days - 1)

previous_mask = (
    (merged_df["TransactionDate"] >= previous_start_date)
    & (merged_df["TransactionDate"] <= previous_end_date)
    & merged_df["TransactionType"].isin(selected_types)
    & merged_df["BranchState"].isin(selected_states)
    & merged_df["AgeGroup"].isin(selected_age_groups)
    & merged_df["AccountType"].isin(selected_account_types)
    & (merged_df["Amount"] >= selected_amount[0])
    & (merged_df["Amount"] <= selected_amount[1])
)
previous_df = merged_df[previous_mask]

# ---------------------------------------------------------------------------
# Helper aggregation utilities (used in many charts)
# ---------------------------------------------------------------------------

def aggregate_by(df: pd.DataFrame, group_col: str, mode: str, metric_label: str = "Metric") -> pd.DataFrame:
    if mode == "Sum":
        agg = df.groupby(group_col)["Amount"].sum().reset_index(name=metric_label)
    else:  # Count
        agg = df.groupby(group_col).size().reset_index(name=metric_label)
    return agg

# ---------------------------------------------------------------------------
# Tabs – Overview, Loans, Recommendations, Raw Data
# ---------------------------------------------------------------------------
tab_overview, tab_loans, tab_recommendations, tab_data = st.tabs([
    "Overview",
    "Loans",
    "Recommendations",
    "Data",
])

# ---------------------------------------------------------------------------
# Overview tab – existing visualisations (unchanged except width params)
# ---------------------------------------------------------------------------
with tab_overview:
    # KPI Metrics
    st.subheader("Key Performance Indicators")
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    
    total_tx = float(len(filtered_df))
    total_volume = float(filtered_df["Amount"].sum())
    avg_ticket = float(filtered_df["Amount"].mean()) if not filtered_df.empty else 0.0
    active_accounts = float(filtered_df["AccountID"].nunique())
    weekend_share = float(filtered_df["IsWeekend"].mean() * 100) if not filtered_df.empty else 0.0

    prev_total_tx = float(len(previous_df))
    prev_total_volume = float(previous_df["Amount"].sum())
    prev_avg_ticket = float(previous_df["Amount"].mean()) if not previous_df.empty else 0.0
    prev_active_accounts = float(previous_df["AccountID"].nunique())
    prev_weekend_share = float(previous_df["IsWeekend"].mean() * 100) if not previous_df.empty else 0.0

    with kpi1:
        st.metric("Transactions", f"{total_tx:,.0f}", delta_label(total_tx, prev_total_tx, "Count"))
    with kpi2:
        st.metric("Volume ($)", f"${total_volume:,.0f}", delta_label(total_volume, prev_total_volume, "Sum"))
    with kpi3:
        st.metric("Avg Ticket ($)", f"${avg_ticket:,.2f}", delta_label(avg_ticket, prev_avg_ticket, "Sum"))
    with kpi4:
        st.metric("Active Accounts", f"{active_accounts:,.0f}", delta_label(active_accounts, prev_active_accounts, "Count"))
    with kpi5:
        weekend_delta = f"{(weekend_share - prev_weekend_share):+.1f} pp vs previous"
        st.metric("Weekend Share", f"{weekend_share:,.1f}%", weekend_delta)

    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top Branches by Volume")
        top_branches = aggregate_by(filtered_df, "BranchName", metric_mode)
        top_branches = top_branches.nlargest(top_n, "Metric")
        fig1 = px.bar(
            top_branches,
            x="BranchName",
            y="Metric",
            color="BranchName",
            height=420,
        )
        st.plotly_chart(fig1, use_container_width=True)
    with col2:
        st.subheader("Top Transaction Types")
        top_types = aggregate_by(filtered_df, "TransactionType", metric_mode)
        top_types = top_types.nlargest(top_n, "Metric")
        fig2 = px.pie(top_types, names="TransactionType", values="Metric", height=420)
        st.plotly_chart(fig2, use_container_width=True)

    # Trend over time (dynamic based on selected grain)
    if time_grain == "Year":
        trend = (
            filtered_df.groupby("Year")["Amount"].sum().reset_index(name="Metric")
        )
        trend["PeriodLabel"] = trend["Year"].astype(str)
        x_label = "Year"
    elif time_grain == "Quarter":
        trend = (
            filtered_df.groupby(["Year", "Quarter"])['Amount']
            .sum()
            .reset_index(name="Metric")
        )
        trend["PeriodLabel"] = trend["Year"].astype(str) + " Q" + trend["Quarter"].astype(str)
        x_label = "Quarter"
    else:  # Month
        trend = (
            filtered_df.groupby(["Year", "MonthName"])['Amount']
            .sum()
            .reset_index(name="Metric")
        )
        trend["PeriodLabel"] = trend["MonthName"] + " " + trend["Year"].astype(str)
        x_label = "Month"
    fig3 = px.line(trend, x="PeriodLabel", y="Metric", markers=True)
    fig3.update_layout(xaxis_title=x_label, yaxis_title=metric_mode)
    st.plotly_chart(fig3, use_container_width=True)

    # Age Group distribution
    age_dist = aggregate_by(filtered_df, "AgeGroup", metric_mode)
    fig4 = px.bar(age_dist, x="AgeGroup", y="Metric", color="AgeGroup")
    st.plotly_chart(fig4, use_container_width=True)

    # Weekend vs Weekday
    weekend_dist = aggregate_by(filtered_df, "IsWeekend", metric_mode, metric_label="Metric")
    weekend_dist["Label"] = weekend_dist["IsWeekend"].map({True: "Weekend", False: "Weekday"})
    fig5 = px.pie(weekend_dist, names="Label", values="Metric")
    st.plotly_chart(fig5, use_container_width=True)

# ---------------------------------------------------------------------------
# Loans tab – loan portfolio analysis
# ---------------------------------------------------------------------------
with tab_loans:
    if loans_df.empty:
        st.info("No loan data available in the current dataset.")
    else:
        st.subheader("Loan Amount Distribution by Type")
        loan_type_amount = (
            loans_df.groupby("LoanType")["PrincipalAmount"]
            .sum()
            .reset_index(name="TotalPrincipal")
        )
        fig_loans1 = px.bar(loan_type_amount, x="LoanType", y="TotalPrincipal", color="LoanType")
        st.plotly_chart(fig_loans1, use_container_width=True)

        st.subheader("Loan Status Overview")
        loan_status = loans_df["Status"].value_counts().reset_index(name="Count")
        loan_status.columns = ["Status", "Count"]
        fig_loans2 = px.pie(loan_status, names="Status", values="Count")
        st.plotly_chart(fig_loans2, use_container_width=True)

        st.subheader("Average Loan Age (Days) by Type")
        avg_age = (
            loans_df.groupby("LoanType")["LoanAgeDays"]
            .mean()
            .reset_index(name="AvgAgeDays")
        )
        fig_loans3 = px.bar(avg_age, x="LoanType", y="AvgAgeDays", color="LoanType")
        st.plotly_chart(fig_loans3, use_container_width=True)

# ---------------------------------------------------------------------------
# Recommendations tab – placeholder (logic unchanged)
# ---------------------------------------------------------------------------
with tab_recommendations:
    st.subheader("Prioritized Business Recommendations")
    recommendations = generate_recommendations(filtered_df, previous_df, merged_df, metric_mode)
    severity_icons = {"High": "🚨", "Medium": "⚠️", "Low": "✅"}
    for rec in recommendations:
        icon = severity_icons.get(rec["severity"], "ℹ️")
        with st.expander(f"{icon} {rec['severity']} - {rec['title']}", expanded=(rec["severity"] == "High")):
            st.markdown(
                f"""
                **Why:** {rec['why']}  
                **Recommended action:** {rec['action']}
                """
            )

# ---------------------------------------------------------------------------
# Data tab – raw filtered data & download
# ---------------------------------------------------------------------------
with tab_data:
    st.subheader("Filtered Transactions")
    view_cols = [
        "TransactionDate",
        "Year",
        "Quarter",
        "MonthName",
        "BranchState",
        "BranchName",
        "TransactionType",
        "AgeGroup",
        "AccountType",
        "AccountStatus",
        "AccountID",
        "Amount",
        "IsWeekend",
    ]
    st.dataframe(
        filtered_df[view_cols].sort_values(by="TransactionDate", ascending=False),
        use_container_width=True,
        height=420,
    )
    csv_data = filtered_df[view_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Filtered Data (CSV)",
        data=csv_data,
        file_name="filtered_transactions.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.caption(
    "Dashboard populated from CSV files (or SQL fallback) with interactive insights and business recommendations."
)
