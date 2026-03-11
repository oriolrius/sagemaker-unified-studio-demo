# Homework: Data Catalog Integration with DataZone

Integrate the ML pipeline with AWS DataZone Data Catalog to enable SQL-based data access.

---

> **IMPORTANT: CLEANUP WHEN FINISHED**
>
> Athena queries incur costs based on data scanned.
>
> **Cost estimate: < $1 for the entire homework** (CSV is small, ~5MB)

---

## Objective

In the current notebooks, data is read directly from S3 using pandas:

```python
df = pd.read_csv(f's3://{bucket}/data/raw/machines.csv')
```

This works, but in enterprise environments, data is typically:

- **Cataloged** in a Data Catalog for discoverability and governance
- **Queried** using SQL for standardization and access control

Your task is to:

1. Register `machines.csv` in the DataZone Data Catalog
2. Identify which notebooks should query the catalog instead of reading S3 directly
3. Modify those notebooks to use SQL queries via `awswrangler`

---

## Learning Objectives

- **Data Governance**: Understand how Data Catalogs enable data discovery and access control
- **SQL in ML Context**: Practice using SQL to extract and filter data for ML pipelines
- **DataZone Features**: Learn the data cataloging capabilities of SageMaker Unified Studio

---

## Prerequisites

- Completed notebooks 01-13 from the ML demo
- Working `.env` file in JupyterLab with `BUCKET_NAME` and `REGION`
- Data uploaded to `s3://{bucket}/data/raw/machines.csv`

---

## Part 1: Create Data Catalog Entry

Register `machines.csv` in the DataZone Data Catalog.

### Option A: Using DataZone UI

1. Navigate to DataZone in SageMaker Unified Studio
2. Create a new Data Source pointing to `s3://{bucket}/data/raw/`
3. Run discovery to detect the CSV schema
4. Publish the asset to the catalog

### Option B: Using DDL (SQL)

Create the table definition manually using Athena:

```sql
CREATE EXTERNAL TABLE IF NOT EXISTS overheat_db.machines (
    timestamp STRING,
    machine_id STRING,
    temperature DOUBLE,
    room_temp DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
LOCATION 's3://{YOUR_BUCKET}/data/raw/'
TBLPROPERTIES ('skip.header.line.count'='1');
```

> **Note**: Replace `{YOUR_BUCKET}` with your actual bucket name.

### Verify the Catalog Entry

Test your catalog entry with a simple query:

```python
import awswrangler as wr

df = wr.athena.read_sql_query(
    sql="SELECT * FROM machines LIMIT 10",
    database="overheat_db"
)
print(df)
```

---

## Part 2: Identify Notebooks to Modify

Review all 13 notebooks and determine which ones should use SQL queries instead of direct S3 reads.

**Your task**: Analyze each notebook and answer:

1. Does this notebook read `machines.csv` from S3?
2. Would it benefit from SQL-based access (filtering, aggregation)?
3. Should it be modified to use the Data Catalog?

**Hints**:

- Not all notebooks read from S3
- Some notebooks read parquet files (leave those unchanged)
- Some notebooks read from local `models/` folder (leave those unchanged)
- Focus only on notebooks that read the raw CSV

Document your analysis in the PDF report.

---

## Part 3: Modify Notebooks to Use SQL

For each notebook you identified, replace the direct S3 read with an `awswrangler` query.

### Before (Direct S3 Read)

```python
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
bucket = os.getenv('BUCKET_NAME')

df = pd.read_csv(f's3://{bucket}/data/raw/machines.csv')
```

### After (Data Catalog Query)

```python
import awswrangler as wr

df = wr.athena.read_sql_query(
    sql="SELECT * FROM machines",
    database="overheat_db"
)
```

### SQL Query Examples

You can use SQL to filter or transform data:

```python
# Get only high temperature readings
df = wr.athena.read_sql_query(
    sql="""
        SELECT * FROM machines
        WHERE temperature > 70
    """,
    database="overheat_db"
)

# Get daily averages per machine
df = wr.athena.read_sql_query(
    sql="""
        SELECT
            machine_id,
            DATE(timestamp) as date,
            AVG(temperature) as avg_temp
        FROM machines
        GROUP BY machine_id, DATE(timestamp)
    """,
    database="overheat_db"
)

# Count readings per machine
df = wr.athena.read_sql_query(
    sql="""
        SELECT machine_id, COUNT(*) as readings
        FROM machines
        GROUP BY machine_id
    """,
    database="overheat_db"
)
```

---

## Part 4: Verify Everything Works

After modifications:

1. Run each modified notebook end-to-end
2. Verify the output matches the original behavior
3. Confirm downstream notebooks still work (they depend on the outputs)

---

## Deliverable: PDF Report

Submit a **single PDF document** named `homework_datacatalog_YOURNAME.pdf` with the following chapters:

### Chapter 1: Data Catalog Setup (2 pages)

- Screenshot of the **Data Catalog entry** in DataZone (or Athena table)
- The **DDL or steps** you used to create the catalog entry
- Screenshot of a **test query** working in a notebook

### Chapter 2: Notebook Analysis (2 pages)

Create a table analyzing ALL 13 notebooks:

| Notebook                  | Reads CSV from S3? | Should Modify? | Reason |
| ------------------------- | ------------------ | -------------- | ------ |
| 01_setup_env.ipynb        | ?                  | ?              | ?      |
| 02_create_s3_bucket.ipynb | ?                  | ?              | ?      |
| ...                       | ...                | ...            | ...    |

Explain your reasoning for each decision.

### Chapter 3: Modified Notebooks (3-4 pages)

For each notebook you modified:

- Screenshot of the **original code** (S3 read)
- Screenshot of the **new code** (SQL query)
- The **SQL query** you used
- Explanation of **why SQL is beneficial** for this specific notebook

### Chapter 4: SQL Queries (2 pages)

Show at least **3 different SQL queries** you wrote:

- One simple SELECT
- One with WHERE filtering
- One with GROUP BY aggregation

For each query:

- The SQL code
- Screenshot of the result
- Explanation of what it does

### Chapter 5: Verification (1 page)

- Screenshot showing **modified notebooks run successfully**
- Confirmation that **downstream notebooks still work**

### Chapter 6: Reflection (1 page)

Answer these questions:

1. What are the benefits of using a Data Catalog vs. direct S3 access?
2. In what scenarios would SQL queries be more useful than pandas operations?
3. What challenges did you encounter and how did you solve them?

---

## Grading Rubric

| Chapter                         | Points | Criteria                                                                              |
| ------------------------------- | ------ | ------------------------------------------------------------------------------------- |
| **1. Data Catalog Setup** | 15     | Catalog entry created correctly, test query works                                     |
| **2. Notebook Analysis**  | 20     | All 13 notebooks analyzed, correct identification of which to modify, clear reasoning |
| **3. Modified Notebooks** | 25     | Correct modifications, SQL queries work, clear before/after comparison                |
| **4. SQL Queries**        | 15     | At least 3 queries shown (SELECT, WHERE, GROUP BY), correct syntax, meaningful use    |
| **5. Verification**       | 10     | Modified notebooks run successfully, downstream dependencies work                     |
| **6. Reflection**         | 15     | Thoughtful answers demonstrating understanding of Data Catalog benefits and SQL in ML |

**Total: 100 points**

---

## Troubleshooting

### "Database not found" error

Make sure you created the database first:

```sql
CREATE DATABASE IF NOT EXISTS overheat_db;
```

### "Table not found" error

Verify the table exists:

```python
import awswrangler as wr
tables = wr.catalog.tables(database="overheat_db")
print(tables)
```

### "Access Denied" error

Your execution role needs permissions for:

- Athena query execution
- Glue Data Catalog access
- S3 read access to the data location

### Query returns wrong data types

The CSV columns are read as strings by default. Cast them in SQL:

```sql
SELECT
    CAST(temperature AS DOUBLE) as temperature,
    CAST(room_temp AS DOUBLE) as room_temp
FROM machines
```

### awswrangler not installed

Install it in the notebook:

```python
!pip install awswrangler
```

---

## Checklist

- [ ] Created Data Catalog entry for `machines.csv`
- [ ] Tested catalog with a simple query
- [ ] Analyzed all 13 notebooks
- [ ] Identified which notebooks to modify
- [ ] Modified notebooks to use `awswrangler` SQL queries
- [ ] Wrote at least 3 different SQL queries
- [ ] Verified modified notebooks run successfully
- [ ] Verified downstream notebooks still work
- [ ] PDF report with all 6 chapters
- [ ] **Cleaned up resources when finished**
