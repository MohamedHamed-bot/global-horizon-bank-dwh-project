from diagrams import Diagram, Cluster, Edge
from diagrams.onprem.database import MSSQL
from diagrams.custom import Custom
from diagrams.programming.language import Python
from diagrams.aws.general import Users
import urllib.request
import os

# Download an icon for Streamlit
streamlit_url = "https://raw.githubusercontent.com/streamlit/streamlit/develop/docs/images/streamlit-mark-color.png"
streamlit_icon = "streamlit.png"
if not os.path.exists(streamlit_icon):
    try:
        urllib.request.urlretrieve(streamlit_url, streamlit_icon)
    except:
        pass

# Modern Graph Attributes
graph_attr = {
    "fontsize": "20",
    "fontname": "Helvetica-bold",
    "bgcolor": "#F4F7F6",
    "pad": "1.0",
    "splines": "spline",
    "nodesep": "1.0",
    "ranksep": "1.5"
}

node_attr = {
    "fontname": "Helvetica",
    "fontsize": "12",
    "fontcolor": "#2C3E50"
}

edge_attr = {
    "color": "#34495E",
    "fontname": "Helvetica",
    "fontsize": "10",
    "fontcolor": "#7F8C8D",
    "penwidth": "2.0"
}

cluster_attr = {
    "bgcolor": "#FFFFFF",
    "pencolor": "#BDC3C7",
    "penwidth": "2.0",
    "fontname": "Helvetica-bold",
    "fontsize": "14",
    "fontcolor": "#2980B9"
}


with Diagram("Global Horizon Bank Data Architecture", show=False, filename="diagrams/data_pipeline", direction="LR", graph_attr=graph_attr, node_attr=node_attr, edge_attr=edge_attr):
    
    users = Users("Bank Customers\n& Operations")
    
    with Cluster("OLTP System (Phase 2-4)", graph_attr=cluster_attr):
        python_gen = Python("Faker & Pandas\nData Generator")
        oltp_db = MSSQL("SQL Server\nTransactional DB")
        
        users >> Edge(label="Daily Transactions") >> oltp_db
        python_gen >> Edge(label="Bulk Insert") >> oltp_db
        
    with Cluster("ETL Process (Phase 5)", graph_attr=cluster_attr):
        etl_procs = MSSQL("Stored Procedures\n(T-SQL)")
        
    with Cluster("Data Warehouse (Phase 6-8)", graph_attr=cluster_attr):
        dwh_db = MSSQL("SQL Server\nStar Schema OLAP")
        
    with Cluster("Analytics & Reporting (Phase 9)", graph_attr=cluster_attr):
        if os.path.exists(streamlit_icon):
            dashboard = Custom("Streamlit App", streamlit_icon)
        else:
            dashboard = Python("Streamlit App")
        analysts = Users("Executive & Analysts")
        
    oltp_db >> Edge(label="Extract (Daily Batch)") >> etl_procs
    etl_procs >> Edge(label="Transform & Load\n(SCD Type 2)") >> dwh_db
    dwh_db >> Edge(label="Aggregate Queries\n(Window Functions)") >> dashboard
    dashboard >> Edge(label="Business Insights") >> analysts
