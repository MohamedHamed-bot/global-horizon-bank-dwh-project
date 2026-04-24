import streamlit as st
import pandas as pd
import plotly.express as px

# Page config
st.set_page_config(page_title="Global Horizon Bank Dashboard", page_icon="🏦", layout="wide")

# Custom CSS for Modern Design
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 1rem;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏦 Global Horizon Bank Analytics")
st.markdown("### Data Warehouse Executive Dashboard")

import pymssql

@st.cache_data(ttl=600)
def load_data():
    try:
        # SQL Server Connection Details
        SERVER = 'localhost:1434'
        USER = 'sa'
        PASSWORD = 'MyStrongPass123!'
        DATABASE = 'GlobalHorizon_DWH'

        conn = pymssql.connect(server=SERVER, user=USER, password=PASSWORD, database=DATABASE)
        
        # Query the Fact Table and join with Dimensions
        query = """
        SELECT 
            ft.TransactionType,
            ft.Amount,
            d.FullDate AS TransactionDate,
            d.Year,
            d.Quarter,
            d.MonthName,
            d.IsWeekend,
            b.BranchName,
            b.State AS BranchState,
            c.AgeGroup,
            a.AccountID,
            a.AccountType,
            a.Status AS AccountStatus
        FROM 
            Fact_Transaction ft
        JOIN Dim_Date d ON ft.DateKey = d.DateKey
        JOIN Dim_Branch b ON ft.BranchKey = b.BranchKey
        JOIN Dim_Customer c ON ft.CustomerKey = c.CustomerKey
        JOIN Dim_Account a ON ft.AccountKey = a.AccountKey
        """
        
        df = pd.read_sql(query, conn)
        
        # For KPI cards, we need total customers and branches logic
        customers_query = "SELECT COUNT(DISTINCT CustomerID) as Count FROM Dim_Customer"
        customers_df = pd.read_sql(customers_query, conn)
        
        branches_query = "SELECT BranchName FROM Dim_Branch"
        branches_df = pd.read_sql(branches_query, conn)
        
        conn.close()
        
        df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
        return df, customers_df, branches_df
        
    except Exception as e:
        st.error(f"Failed to connect to SQL Server. Ensure Docker container is running on port 1434.\n{e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, customers_df, branches_df = load_data()

if df.empty:
    st.error("No data found in Data Warehouse. Run `python src/setup_sqlserver.py` to populate it.")
    st.stop()

# -----------------------------
# Interactive Filters
# -----------------------------
st.sidebar.header("Filters")

min_date = df["TransactionDate"].min().date()
max_date = df["TransactionDate"].max().date()
date_range = st.sidebar.date_input(
    "Transaction Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Streamlit may return a single date if user clears/edits input.
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

transaction_types = sorted(df["TransactionType"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect(
    "Transaction Type",
    options=transaction_types,
    default=transaction_types
)

branch_options = sorted(df["BranchName"].dropna().unique().tolist())
selected_branches = st.sidebar.multiselect(
    "Branch",
    options=branch_options,
    default=branch_options
)

state_options = sorted(df["BranchState"].dropna().unique().tolist())
selected_states = st.sidebar.multiselect(
    "Branch State",
    options=state_options,
    default=state_options
)

age_group_options = sorted(df["AgeGroup"].dropna().unique().tolist())
selected_age_groups = st.sidebar.multiselect(
    "Age Group",
    options=age_group_options,
    default=age_group_options
)

account_type_options = sorted(df["AccountType"].dropna().unique().tolist())
selected_account_types = st.sidebar.multiselect(
    "Account Type",
    options=account_type_options,
    default=account_type_options
)

account_status_options = sorted(df["AccountStatus"].dropna().unique().tolist())
selected_account_statuses = st.sidebar.multiselect(
    "Account Status",
    options=account_status_options,
    default=account_status_options
)

amount_min = float(df["Amount"].min())
amount_max = float(df["Amount"].max())
selected_amount = st.sidebar.slider(
    "Amount Range ($)",
    min_value=amount_min,
    max_value=amount_max,
    value=(amount_min, amount_max)
)

filtered_df = df[
    (df["TransactionDate"].dt.date >= start_date)
    & (df["TransactionDate"].dt.date <= end_date)
    & (df["TransactionType"].isin(selected_types))
    & (df["BranchName"].isin(selected_branches))
    & (df["BranchState"].isin(selected_states))
    & (df["AgeGroup"].isin(selected_age_groups))
    & (df["AccountType"].isin(selected_account_types))
    & (df["AccountStatus"].isin(selected_account_statuses))
    & (df["Amount"] >= selected_amount[0])
    & (df["Amount"] <= selected_amount[1])
].copy()

if filtered_df.empty:
    st.warning("No records match current filters. Adjust the filters in the sidebar.")
    st.stop()

# Key Metrics (dynamic with filters)
col1, col2, col3, col4, col5 = st.columns(5)
total_tx = len(filtered_df)
total_volume = filtered_df["Amount"].sum()
avg_ticket = filtered_df["Amount"].mean()
active_accounts = filtered_df["AccountID"].nunique()
weekend_share = (filtered_df["IsWeekend"].mean() * 100) if not filtered_df.empty else 0.0

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Transactions</div><div class="metric-value">{total_tx:,.0f}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Volume ($)</div><div class="metric-value">${total_volume:,.2f}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Average Ticket ($)</div><div class="metric-value">${avg_ticket:,.2f}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Active Accounts</div><div class="metric-value">{active_accounts:,.0f}</div></div>', unsafe_allow_html=True)
with col5:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Weekend Share (%)</div><div class="metric-value">{weekend_share:,.1f}%</div></div>', unsafe_allow_html=True)

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Overview", "Behavior Analysis", "Data Explorer"])

with tab1:
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader("Transaction Volume by Type")
        tx_type_vol = filtered_df.groupby("TransactionType", as_index=False)["Amount"].sum()
        fig1 = px.pie(
            tx_type_vol,
            values="Amount",
            names="TransactionType",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig1, width="stretch")

    with col_chart2:
        st.subheader("Monthly Transaction Trend")
        monthly_data = filtered_df.copy()
        monthly_data["MonthYear"] = monthly_data["TransactionDate"].dt.to_period("M").astype(str)
        monthly_trend = monthly_data.groupby("MonthYear", as_index=False)["Amount"].sum()
        fig2 = px.line(monthly_trend, x="MonthYear", y="Amount", markers=True, line_shape="spline")
        fig2.update_traces(line_color="#1f77b4", line_width=3)
        st.plotly_chart(fig2, width="stretch")

    col_chart3, col_chart4 = st.columns(2)
    with col_chart3:
        st.subheader("Top Branches by Volume")
        branch_vol = (
            filtered_df.groupby("BranchName", as_index=False)["Amount"]
            .sum()
            .sort_values(by="Amount", ascending=False)
            .head(10)
        )
        fig3 = px.bar(
            branch_vol,
            x="Amount",
            y="BranchName",
            orientation="h",
            color="Amount",
            color_continuous_scale="Blues"
        )
        fig3.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig3, width="stretch")

    with col_chart4:
        st.subheader("Customer Demographics (Age Group)")
        age_dist = filtered_df["AgeGroup"].value_counts(dropna=False).reset_index()
        age_dist.columns = ["AgeGroup", "Count"]
        fig4 = px.bar(
            age_dist,
            x="AgeGroup",
            y="Count",
            color="AgeGroup",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig4, width="stretch")

with tab2:
    col_behavior1, col_behavior2 = st.columns(2)

    with col_behavior1:
        st.subheader("Branch x Transaction Type Heatmap")
        heatmap_data = (
            filtered_df.groupby(["BranchName", "TransactionType"], as_index=False)["Amount"]
            .sum()
        )
        fig5 = px.density_heatmap(
            heatmap_data,
            x="TransactionType",
            y="BranchName",
            z="Amount",
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig5, width="stretch")

    with col_behavior2:
        st.subheader("Transaction Distribution by Type")
        fig6 = px.box(
            filtered_df,
            x="TransactionType",
            y="Amount",
            color="TransactionType",
            points="outliers"
        )
        st.plotly_chart(fig6, width="stretch")

    col_behavior3, col_behavior4 = st.columns(2)
    with col_behavior3:
        st.subheader("Volume by Account Type")
        acct_type_vol = filtered_df.groupby("AccountType", as_index=False)["Amount"].sum()
        fig8 = px.bar(acct_type_vol, x="AccountType", y="Amount", color="AccountType")
        st.plotly_chart(fig8, width="stretch")

    with col_behavior4:
        st.subheader("State-level Performance")
        state_vol = filtered_df.groupby("BranchState", as_index=False)["Amount"].sum()
        fig9 = px.treemap(state_vol, path=["BranchState"], values="Amount", color="Amount", color_continuous_scale="Blues")
        st.plotly_chart(fig9, width="stretch")

    st.subheader("Daily Activity Timeline")
    daily_data = filtered_df.copy()
    daily_data["Date"] = daily_data["TransactionDate"].dt.date
    daily_data = daily_data.groupby("Date", as_index=False)["Amount"].sum()
    fig7 = px.area(daily_data, x="Date", y="Amount")
    st.plotly_chart(fig7, width="stretch")

with tab3:
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
        "Amount"
    ]
    st.dataframe(
        filtered_df[view_cols].sort_values(by="TransactionDate", ascending=False),
        width="stretch",
        height=420
    )

    csv_data = filtered_df[view_cols].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download Filtered Data (CSV)",
        data=csv_data,
        file_name="filtered_transactions.csv",
        mime="text/csv"
    )

    with st.expander("Filter Summary"):
        st.write(
            f"Date: {start_date} to {end_date} | "
            f"Types: {len(selected_types)} | "
            f"Branches: {len(selected_branches)} | "
            f"States: {len(selected_states)} | "
            f"Age Groups: {len(selected_age_groups)} | "
            f"Account Types: {len(selected_account_types)} | "
            f"Amount: ${selected_amount[0]:,.2f} - ${selected_amount[1]:,.2f}"
        )

st.markdown("---")
st.caption("Dashboard populated from simulated DWH Data. Phase 9 Analytics Complete.")
