# SQL Implementation Guide

This document provides an in-depth look at the SQL architecture, design decisions, and execution strategies used in the Global Horizon Bank project.

## 1. OLTP Database Architecture (Transactional)

The `GlobalHorizon_OLTP` database is designed in the **Third Normal Form (3NF)** to ensure zero data redundancy and optimal write performance for daily banking operations.

### Key Features:
- **Constraints**: Extensive use of `CHECK` constraints (e.g., ensuring `Amount > 0` and `Status IN ('Active', 'Closed')`) to maintain data integrity at the database level before business logic evaluates it.
- **Data Types**: Strict usage of `DECIMAL(18,2)` for financial precision and `UNIQUEIDENTIFIER` for Transaction IDs to prevent sequential guessing.
- **Relationships**: A Many-to-Many junction table (`Account_Customers`) handles joint accounts, a critical real-world banking requirement.

## 2. ETL Process (Extract, Transform, Load)

The ETL pipeline bridges the OLTP and OLAP systems. It is built entirely within SQL Server using **Stored Procedures**.

### Design Pattern:
- **Incremental Loading**: The `sp_ETL_Fact_Transaction` procedure uses a `NOT EXISTS` clause to only load new transactions that arrived since the last batch. This prevents rebuilding the entire data warehouse daily.
- **Data Cleansing & Transformation**: In `sp_ETL_Dim_Customer`, the raw `DateOfBirth` from the OLTP system is transformed on-the-fly into an `AgeGroup` categorical bucket (e.g., '25-35'), making it immediately ready for analytical slicing.

## 3. OLAP Database Architecture (Data Warehouse)

The `GlobalHorizon_DWH` uses a **Star Schema** to prioritize read-heavy analytical performance over write efficiency.

### Advanced Concepts:
- **Surrogate Keys**: `IDENTITY` columns (e.g., `CustomerKey`) are used instead of business keys (`CustomerID`) to insulate the data warehouse from operational system changes.
- **Slowly Changing Dimensions (SCD Type 2)**: The `Dim_Customer` table tracks geographical history. If a customer moves from NY to CA, the old record is expired (`IsCurrent = 0`) and a new record is created. This ensures historical transactions remain tied to NY, while new ones tie to CA.
- **Degenerate Dimensions**: The `TransactionID` in the Fact table serves as a degenerate dimension, providing a direct link back to the OLTP system for auditing without requiring a separate dimension table.

## 4. Performance Tuning Strategy

To handle the "Big Data" scale (millions of rows):
- **Table Partitioning**: The `Fact_Transaction` table is logically partitioned by `Year`. A query requesting "2023 Revenue" will utilize **Partition Pruning**, physically scanning only the 2023 data blocks and ignoring the rest.
- **Columnstore Indexes**: A `CLUSTERED COLUMNSTORE INDEX` is applied to the Fact table. Unlike traditional B-Trees that store data row-by-row, this stores data column-by-column, allowing massive aggregations (`SUM`, `COUNT`) to execute in milliseconds by scanning highly compressed columnar blocks.
