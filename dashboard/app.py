import streamlit as st
import pandas as pd
import plotly.express as px
import os
import random
from typing import Tuple

try:
    import pymssql
    _PYMSSQL_AVAILABLE = True
except ImportError:
    _PYMSSQL_AVAILABLE = False

# Page config
st.set_page_config(page_title="Global Horizon Bank Dashboard", page_icon="🏦", layout="wide")

st.title("🏦 Global Horizon Bank Analytics")
st.markdown("### Data Warehouse Executive Dashboard")


@st.cache_data(ttl=600)
def build_demo_dataset(rows: int = 12000) -> pd.DataFrame:
    random.seed(42)
    date_range = pd.date_range(start="2023-01-01", end="2026-12-31", freq="D")
    transaction_types = ["Deposit", "Withdrawal", "Transfer", "Payment"]
    branches = [
        ("Downtown Branch", "NY"),
        ("Riverside Branch", "CA"),
        ("Central Branch", "TX"),
        ("North Branch", "IL"),
        ("Lakeside Branch", "FL"),
        ("Metro Branch", "WA"),
        ("West Branch", "AZ"),
        ("Capital Branch", "VA"),
    ]
    age_groups = ["18-24", "25-35", "36-50", "51+"]
    account_types = ["Savings", "Checking", "Business", "Credit"]
    account_statuses = ["Active", "Inactive", "Dormant"]

    records = []
    for _ in range(rows):
        tx_date = random.choice(date_range)
        branch_name, branch_state = random.choice(branches)
        tx_type = random.choices(
            transaction_types,
            weights=[0.30, 0.28, 0.24, 0.18],
            k=1
        )[0]
        amount = round(random.uniform(25, 5000), 2)
        records.append(
            {
                "TransactionType": tx_type,
                "Amount": amount,
                "TransactionDate": tx_date,
                "Year": tx_date.year,
                "Quarter": ((tx_date.month - 1) // 3) + 1,
                "MonthName": tx_date.strftime("%B"),
                "IsWeekend": 1 if tx_date.weekday() >= 5 else 0,
                "BranchName": branch_name,
                "BranchState": branch_state,
                "AgeGroup": random.choice(age_groups),
                "AccountID": random.randint(100000, 150000),
                "AccountType": random.choice(account_types),
                "AccountStatus": random.choices(account_statuses, weights=[0.84, 0.10, 0.06], k=1)[0],
            }
        )
    return pd.DataFrame.from_records(records)


@st.cache_data(ttl=600)
def load_data() -> Tuple[pd.DataFrame, str]:
    server = os.getenv("SQLSERVER_HOST", "localhost")
    port = int(os.getenv("SQLSERVER_PORT", "21433"))
    user = os.getenv("SQLSERVER_USER", "sa")
    password = os.getenv("SQLSERVER_PASSWORD", "MyStrongPass123!")
    database = os.getenv("SQLSERVER_DB", "GlobalHorizon_DWH")
    runtime_env = os.getenv("STREAMLIT_ENV", "development").strip().lower()
    require_sql_in_production = os.getenv("REQUIRE_SQL_IN_PRODUCTION", "true").strip().lower() == "true"

    # Streamlit Cloud can provide these values via Secrets.
    if hasattr(st, "secrets"):
        server = st.secrets.get("SQLSERVER_HOST", server)
        port = int(st.secrets.get("SQLSERVER_PORT", port))
        user = st.secrets.get("SQLSERVER_USER", user)
        password = st.secrets.get("SQLSERVER_PASSWORD", password)
        database = st.secrets.get("SQLSERVER_DB", database)
        runtime_env = st.secrets.get("STREAMLIT_ENV", runtime_env).strip().lower()
        require_sql_in_production = (
            str(st.secrets.get("REQUIRE_SQL_IN_PRODUCTION", require_sql_in_production)).strip().lower() == "true"
        )

    try:
        if not _PYMSSQL_AVAILABLE:
            raise ImportError("pymssql is not installed in this environment.")
        conn = pymssql.connect(
            server=server,
            port=port,
            user=user,
            password=password,
            database=database
        )
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
        FROM Fact_Transaction ft
        JOIN Dim_Date d ON ft.DateKey = d.DateKey
        JOIN Dim_Branch b ON ft.BranchKey = b.BranchKey
        JOIN Dim_Customer c ON ft.CustomerKey = c.CustomerKey
        JOIN Dim_Account a ON ft.AccountKey = a.AccountKey
        """
        dataframe = pd.read_sql(query, conn)
        conn.close()
        dataframe["TransactionDate"] = pd.to_datetime(dataframe["TransactionDate"])
        return dataframe, "sql"
    except Exception as exc:
        is_production = runtime_env == "production"
        if is_production and require_sql_in_production:
            st.error(
                "SQL connection is required in production but is currently unavailable. "
                "Please configure valid SQL Server access in Streamlit secrets."
            )
            st.caption("Expected secrets: SQLSERVER_HOST, SQLSERVER_PORT, SQLSERVER_USER, SQLSERVER_PASSWORD, SQLSERVER_DB")
            st.stop()

        st.warning("SQL connection is unavailable. Running in demo mode (development fallback).")
        st.caption(f"Connection details attempted: `{server}:{port}`.")
        demo_df = build_demo_dataset()
        demo_df["TransactionDate"] = pd.to_datetime(demo_df["TransactionDate"])
        return demo_df, "demo"


def metric_value(dataframe: pd.DataFrame, mode: str) -> float:
    if dataframe.empty:
        return 0.0
    if mode == "Amount":
        return float(dataframe["Amount"].sum())
    return float(len(dataframe))


def delta_label(current_value: float, previous_value: float, mode: str) -> str:
    if previous_value == 0:
        return "n/a vs previous"
    delta_pct = ((current_value - previous_value) / previous_value) * 100
    unit = "amount" if mode == "Amount" else "count"
    return f"{delta_pct:+.1f}% vs previous {unit}"


def aggregate_by(dataframe: pd.DataFrame, group_col: str, mode: str, metric_label: str = "Metric") -> pd.DataFrame:
    if mode == "Amount":
        grouped = dataframe.groupby(group_col, as_index=False)["Amount"].sum()
        return grouped.rename(columns={"Amount": metric_label})
    grouped = dataframe.groupby(group_col, as_index=False).size().rename(columns={"size": metric_label})
    return grouped


def build_temporal_trend(dataframe: pd.DataFrame, grain: str, mode: str) -> pd.DataFrame:
    trend_df = dataframe.copy()
    if grain == "Day":
        trend_df["PeriodLabel"] = trend_df["TransactionDate"].dt.strftime("%Y-%m-%d")
        trend_df["PeriodSort"] = trend_df["TransactionDate"].dt.normalize()
    elif grain == "Week":
        week_start = trend_df["TransactionDate"].dt.to_period("W").dt.start_time
        trend_df["PeriodLabel"] = week_start.dt.strftime("%Y-%m-%d")
        trend_df["PeriodSort"] = week_start
    elif grain == "Month":
        month_start = trend_df["TransactionDate"].dt.to_period("M").dt.start_time
        trend_df["PeriodLabel"] = month_start.dt.strftime("%Y-%m")
        trend_df["PeriodSort"] = month_start
    else:
        quarter_start = trend_df["TransactionDate"].dt.to_period("Q").dt.start_time
        trend_df["PeriodLabel"] = trend_df["TransactionDate"].dt.to_period("Q").astype(str)
        trend_df["PeriodSort"] = quarter_start

    grouped = aggregate_by(trend_df, "PeriodLabel", mode, metric_label="Metric")
    sort_map = trend_df[["PeriodLabel", "PeriodSort"]].drop_duplicates()
    grouped = grouped.merge(sort_map, on="PeriodLabel", how="left").sort_values("PeriodSort")
    return grouped


def generate_recommendations(
    current_df: pd.DataFrame,
    previous_df: pd.DataFrame,
    full_df: pd.DataFrame,
    mode: str,
) -> list[dict]:
    recommendations = []
    current_metric = metric_value(current_df, mode)
    previous_metric = metric_value(previous_df, mode)
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
                "action": "Allocate service capacity to high-growth states and transaction types."
            })

    if current_avg_ticket > 0 and global_avg_ticket > 0 and current_avg_ticket >= (global_avg_ticket * 1.2):
        recommendations.append({
            "severity": "Medium",
            "title": "Launch premium offers for high-value segments",
            "why": f"Average ticket (${current_avg_ticket:,.2f}) exceeds global baseline (${global_avg_ticket:,.2f}).",
            "action": "Promote premium bundles and relationship-driven products for this segment."
        })

    tx_mix = aggregate_by(current_df, "TransactionType", "Transaction Count", metric_label="TxCount")
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


df, data_source = load_data()
if df.empty:
    st.error("No data was loaded. Check SQL credentials or demo data generation.")
    st.stop()

if data_source == "sql":
    st.success("Connected to SQL Server DWH.")
else:
    st.info("Using demo mode because SQL is unavailable and fallback is enabled for non-production use.")

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
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

transaction_types = sorted(df["TransactionType"].dropna().unique().tolist())
selected_types = st.sidebar.multiselect("Transaction Type", options=transaction_types, default=transaction_types)
branch_options = sorted(df["BranchName"].dropna().unique().tolist())
selected_branches = st.sidebar.multiselect("Branch", options=branch_options, default=branch_options)
state_options = sorted(df["BranchState"].dropna().unique().tolist())
selected_states = st.sidebar.multiselect("Branch State", options=state_options, default=state_options)
age_group_options = sorted(df["AgeGroup"].dropna().unique().tolist())
selected_age_groups = st.sidebar.multiselect("Age Group", options=age_group_options, default=age_group_options)
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

st.sidebar.markdown("---")
st.sidebar.subheader("Analysis Controls")
metric_mode = st.sidebar.radio(
    "Metric Mode",
    options=["Amount", "Transaction Count"],
    index=0,
    help="Controls chart aggregation and recommendation scoring."
)
time_grain = st.sidebar.selectbox(
    "Trend Time Grain",
    options=["Day", "Week", "Month", "Quarter"],
    index=2
)
top_n = st.sidebar.slider("Top N Branches", min_value=5, max_value=25, value=10)

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

period_days = max((end_date - start_date).days + 1, 1)
previous_end_date = pd.Timestamp(start_date) - pd.Timedelta(days=1)
previous_start_date = previous_end_date - pd.Timedelta(days=period_days - 1)
previous_df = df[
    (df["TransactionDate"].dt.date >= previous_start_date.date())
    & (df["TransactionDate"].dt.date <= previous_end_date.date())
    & (df["TransactionType"].isin(selected_types))
    & (df["BranchName"].isin(selected_branches))
    & (df["BranchState"].isin(selected_states))
    & (df["AgeGroup"].isin(selected_age_groups))
    & (df["AccountType"].isin(selected_account_types))
    & (df["AccountStatus"].isin(selected_account_statuses))
    & (df["Amount"] >= selected_amount[0])
    & (df["Amount"] <= selected_amount[1])
].copy()

# Key Metrics
col1, col2, col3, col4, col5 = st.columns(5)
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

with col1:
    st.metric("Transactions", f"{total_tx:,.0f}", delta_label(total_tx, prev_total_tx, "Transaction Count"))
with col2:
    st.metric("Volume ($)", f"${total_volume:,.2f}", delta_label(total_volume, prev_total_volume, "Amount"))
with col3:
    st.metric("Average Ticket ($)", f"${avg_ticket:,.2f}", delta_label(avg_ticket, prev_avg_ticket, "Amount"))
with col4:
    st.metric(
        "Active Accounts",
        f"{active_accounts:,.0f}",
        delta_label(active_accounts, prev_active_accounts, "Transaction Count")
    )
with col5:
    weekend_delta = f"{(weekend_share - prev_weekend_share):+.1f} pp vs previous"
    st.metric("Weekend Share (%)", f"{weekend_share:,.1f}%", weekend_delta)

st.markdown("---")

metric_axis_label = "Amount ($)" if metric_mode == "Amount" else "Transaction Count"
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Behavior Analysis", "Business Recommendations", "Data Explorer"])

with tab1:
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.subheader(f"{metric_axis_label} by Transaction Type")
        tx_type_vol = aggregate_by(filtered_df, "TransactionType", metric_mode, metric_label="Metric")
        fig1 = px.pie(
            tx_type_vol,
            values="Metric",
            names="TransactionType",
            hole=0.45,
            color_discrete_sequence=px.colors.sequential.RdBu
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        st.subheader(f"{time_grain} Transaction Trend")
        trend = build_temporal_trend(filtered_df, time_grain, metric_mode)
        fig2 = px.line(trend, x="PeriodLabel", y="Metric", markers=True, line_shape="spline")
        fig2.update_traces(line_color="#1f77b4", line_width=3)
        fig2.update_layout(xaxis_title=time_grain, yaxis_title=metric_axis_label)
        st.plotly_chart(fig2, use_container_width=True)

    col_chart3, col_chart4 = st.columns(2)
    with col_chart3:
        st.subheader(f"Top {top_n} Branches by {metric_axis_label}")
        branch_vol = aggregate_by(filtered_df, "BranchName", metric_mode, metric_label="Metric")
        branch_vol = branch_vol.sort_values(by="Metric", ascending=False).head(top_n)
        fig3 = px.bar(
            branch_vol,
            x="Metric",
            y="BranchName",
            orientation="h",
            color="Metric",
            color_continuous_scale="Blues"
        )
        fig3.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig3, use_container_width=True)

    with col_chart4:
        st.subheader(f"Customer Demographics by Age Group ({metric_axis_label})")
        age_dist = aggregate_by(filtered_df, "AgeGroup", metric_mode, metric_label="Metric")
        fig4 = px.bar(
            age_dist,
            x="AgeGroup",
            y="Metric",
            color="AgeGroup",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig4, use_container_width=True)

with tab2:
    col_behavior1, col_behavior2 = st.columns(2)
    with col_behavior1:
        st.subheader(f"Branch x Transaction Type Heatmap ({metric_axis_label})")
        if metric_mode == "Amount":
            heatmap_data = filtered_df.groupby(["BranchName", "TransactionType"], as_index=False)["Amount"].sum()
            z_field = "Amount"
        else:
            heatmap_data = filtered_df.groupby(["BranchName", "TransactionType"], as_index=False).size()
            heatmap_data = heatmap_data.rename(columns={"size": "TxCount"})
            z_field = "TxCount"
        fig5 = px.density_heatmap(
            heatmap_data,
            x="TransactionType",
            y="BranchName",
            z=z_field,
            color_continuous_scale="Viridis"
        )
        st.plotly_chart(fig5, use_container_width=True)

    with col_behavior2:
        st.subheader("Transaction Distribution by Type")
        fig6 = px.box(
            filtered_df,
            x="TransactionType",
            y="Amount",
            color="TransactionType",
            points="outliers"
        )
        st.plotly_chart(fig6, use_container_width=True)

    col_behavior3, col_behavior4 = st.columns(2)
    with col_behavior3:
        st.subheader(f"{metric_axis_label} by Account Type")
        acct_type_vol = aggregate_by(filtered_df, "AccountType", metric_mode, metric_label="Metric")
        fig8 = px.bar(acct_type_vol, x="AccountType", y="Metric", color="AccountType")
        st.plotly_chart(fig8, use_container_width=True)

    with col_behavior4:
        st.subheader(f"State-level Performance ({metric_axis_label})")
        state_vol = aggregate_by(filtered_df, "BranchState", metric_mode, metric_label="Metric")
        fig9 = px.treemap(
            state_vol,
            path=["BranchState"],
            values="Metric",
            color="Metric",
            color_continuous_scale="Blues"
        )
        st.plotly_chart(fig9, use_container_width=True)

    st.subheader(f"{time_grain} Activity Timeline")
    timeline = build_temporal_trend(filtered_df, time_grain, metric_mode)
    fig7 = px.area(timeline, x="PeriodLabel", y="Metric")
    fig7.update_layout(xaxis_title=time_grain, yaxis_title=metric_axis_label)
    st.plotly_chart(fig7, use_container_width=True)

with tab3:
    st.subheader("Prioritized Business Recommendations")
    recommendations = generate_recommendations(filtered_df, previous_df, df, metric_mode)
    severity_icons = {"High": "🚨", "Medium": "⚠️", "Low": "✅"}
    for rec in recommendations:
        icon = severity_icons.get(rec["severity"], "ℹ️")
        st.markdown(
            f"""
            **{icon} {rec['severity']} - {rec['title']}**  
            **Why:** {rec['why']}  
            **Recommended action:** {rec['action']}
            """
        )

with tab4:
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
        use_container_width=True,
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
            f"Amount: ${selected_amount[0]:,.2f} - ${selected_amount[1]:,.2f} | "
            f"Metric Mode: {metric_mode} | Grain: {time_grain} | Top N: {top_n}"
        )

st.markdown("---")
st.caption("Dashboard populated from SQL Server DWH with interactive insights and rule-based recommendations.")
