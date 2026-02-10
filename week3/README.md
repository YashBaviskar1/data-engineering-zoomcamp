
# Module 3 Homework – Data Warehousing & BigQuery

This repository contains a local, reproducible solution to the **Module 3 Homework** using the **NYC Yellow Taxi Trip Records (January–June 2024)**.
---

## Dataset

* NYC Yellow Taxi Trip Records
* Period: January 2024 – June 2024
* Format: Parquet
* Source: [https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)

---

## Table Definitions (BigQuery)

### External Table (Parquet in GCS)

```sql
CREATE OR REPLACE EXTERNAL TABLE dataset.yellow_taxi_external
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://<bucket_name>/yellow_tripdata_2024-*.parquet']
);
```

### Materialized Table

```sql
CREATE OR REPLACE TABLE dataset.yellow_taxi
AS
SELECT *
FROM dataset.yellow_taxi_external;
```

---

## Question 1 – Count of Records

**SQL**

```sql
SELECT COUNT(*) 
FROM dataset.yellow_taxi;
```

**Answer**

20,332,093

---

## Question 2 – Estimated Data Read (External vs Materialized Table)

**SQL**

```sql
SELECT COUNT(DISTINCT PULocationID)
FROM dataset.yellow_taxi_external;

SELECT COUNT(DISTINCT PULocationID)
FROM dataset.yellow_taxi;
```

**Answer**

0 MB for the External Table and 155.12 MB for the Materialized Table

---

## Question 3 – Columnar Storage Behavior

**SQL (one column)**

```sql
SELECT PULocationID
FROM dataset.yellow_taxi;
```

**SQL (two columns)**

```sql
SELECT PULocationID, DOLocationID
FROM dataset.yellow_taxi;
```

**Answer**

BigQuery is a columnar database and only scans the columns requested by the query. Selecting two columns requires reading more data than selecting one column, resulting in higher estimated bytes processed.

---

## Question 4 – Zero Fare Trips

**SQL**

```sql
SELECT COUNT(*)
FROM dataset.yellow_taxi
WHERE fare_amount = 0;
```

**Answer**

8,333

---

## Question 5 – Optimized Table Strategy

Query pattern:

* Filter on `tpep_dropoff_datetime`
* Order by `VendorID`

**Optimized Table**

```sql
CREATE OR REPLACE TABLE dataset.yellow_taxi_partitioned
PARTITION BY DATE(tpep_dropoff_datetime)
CLUSTER BY VendorID
AS
SELECT *
FROM dataset.yellow_taxi;
```

**Answer**

Partition by `tpep_dropoff_datetime` and cluster on `VendorID`.

---

## Question 6 – Partition Benefits

**SQL (Non-partitioned table)**

```sql
SELECT DISTINCT VendorID
FROM dataset.yellow_taxi
WHERE tpep_dropoff_datetime BETWEEN
      '2024-03-01' AND '2024-03-15 23:59:59';
```

**SQL (Partitioned table)**

```sql
SELECT DISTINCT VendorID
FROM dataset.yellow_taxi_partitioned
WHERE tpep_dropoff_datetime BETWEEN
      '2024-03-01' AND '2024-03-15 23:59:59';
```

**Answer**

310.24 MB for the non-partitioned table and 26.84 MB for the partitioned table

---

## Question 7 – External Table Storage Location

**Answer**

GCP Bucket

---

## Question 8 – Clustering Best Practice

**Answer**

False

Clustering should be applied only when query patterns justify it.

---

## Question 9 – COUNT(*) Table Scan

**SQL**

```sql
SELECT COUNT(*)
FROM dataset.yellow_taxi;
```

**Explanation**

`COUNT(*)` requires scanning all rows in the table. Without a partition filter, BigQuery cannot prune data, resulting in a full table scan approximately equal to the table size.

---
