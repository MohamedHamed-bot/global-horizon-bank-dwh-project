import streamlit as st
import pandas as pd
import plotly.express as px
import os

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

@st.cache_data
def load_data():
    data_dir = '../data/raw'
    try:
        transactions = pd.read_csv(f"{data_dir}/transactions.csv")
        customers = pd.read_csv(f"{data_dir}/customers.csv")
        accounts = pd.read_csv(f"{data_dir}/accounts.csv")
        branches = pd.read_csv(f"{data_dir}/branches.csv")
        
        # Merge for OLAP-like view
        df = transactions.merge(accounts, on='AccountID')
        df = df.merge(customers, on='CustomerID')
        df = df.merge(branches, on='BranchID')
        df['TransactionDate'] = pd.to_datetime(df['TransactionDate'])
        return df, customers, branches
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df, customers_df, branches_df = load_data()

if df.empty:
    st.error("Data not found. Please ensure the data generation script has been run.")
    st.stop()

# Key Metrics
col1, col2, col3, col4 = st.columns(4)

total_tx = len(df)
total_volume = df['Amount'].sum()
total_customers = len(customers_df)
active_accounts = len(df['AccountID'].unique())

with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Transactions</div><div class="metric-value">{total_tx:,.0f}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Volume ($)</div><div class="metric-value">${total_volume:,.2f}</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Total Customers</div><div class="metric-value">{total_customers:,.0f}</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-label">Active Accounts Transacting</div><div class="metric-value">{active_accounts:,.0f}</div></div>', unsafe_allow_html=True)

st.markdown("---")

# Visualizations
col_chart1, col_chart2 = st.columns(2)

with col_chart1:
    st.subheader("Transaction Volume by Type")
    tx_type_vol = df.groupby('TransactionType')['Amount'].sum().reset_index()
    fig1 = px.pie(tx_type_vol, values='Amount', names='TransactionType', hole=0.4, color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig1, use_container_width=True)

with col_chart2:
    st.subheader("Monthly Transaction Trend")
    df['MonthYear'] = df['TransactionDate'].dt.to_period('M').astype(str)
    monthly_trend = df.groupby('MonthYear')['Amount'].sum().reset_index()
    fig2 = px.line(monthly_trend, x='MonthYear', y='Amount', markers=True, line_shape='spline')
    fig2.update_traces(line_color='#1f77b4', line_width=3)
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("---")
col_chart3, col_chart4 = st.columns(2)

with col_chart3:
    st.subheader("Top Branches by Volume")
    branch_vol = df.groupby('BranchName')['Amount'].sum().reset_index().sort_values(by='Amount', ascending=False).head(10)
    fig3 = px.bar(branch_vol, x='Amount', y='BranchName', orientation='h', color='Amount', color_continuous_scale='Blues')
    fig3.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig3, use_container_width=True)

with col_chart4:
    st.subheader("Customer Demographics (Age Group Approximation)")
    customers_df['Age'] = pd.to_datetime('today').year - pd.to_datetime(customers_df['DateOfBirth']).dt.year
    bins = [18, 25, 35, 50, 65, 100]
    labels = ['18-24', '25-34', '35-49', '50-64', '65+']
    customers_df['AgeGroup'] = pd.cut(customers_df['Age'], bins=bins, labels=labels, right=False)
    age_dist = customers_df['AgeGroup'].value_counts().reset_index()
    age_dist.columns = ['AgeGroup', 'Count']
    fig4 = px.bar(age_dist, x='AgeGroup', y='Count', color='AgeGroup', color_discrete_sequence=px.colors.qualitative.Pastel)
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.caption("Dashboard populated from simulated DWH Data. Phase 9 Analytics Complete.")
