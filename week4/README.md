## Analytics Engineering basics 





### What is dbt?
dbt is a transformation workflow that allows anyone that knows SQL to deploy analytics code following software engineering best practices like modularity, portablity, CI/CD and documentation




# Module 4 – Analytics Engineering with dbt (NYC Taxi Data)

## Overview

This project implements an end-to-end analytics engineering workflow using **dbt Core** and **DuckDB** on NYC Taxi data (Green, Yellow, and FHV trips). The goal was to transform raw trip-level data into analytics-ready fact and dimension models, enforce data quality through tests, understand model lineage, and answer business-level analytical questions.

This module emphasized conceptual clarity around:

* ELT-based transformation workflows
* dbt model layering (staging → intermediate → marts)
* Data lineage and dependency resolution
* Generic data tests and data quality enforcement
* Fact table aggregation
* Source configuration and raw data governance
* Warehouse resource constraints in local execution environments

The project was executed entirely locally using DuckDB as the analytical engine and dbt Core for transformation orchestration.

---

## Architecture Overview

The transformation pipeline follows a layered analytics engineering structure:

### 1. Raw Layer (Sources)

Raw trip data is ingested into DuckDB under the `prod` schema:

* `green_tripdata`
* `yellow_tripdata`
* `fhv_tripdata`

These are declared explicitly in `sources.yml`, allowing dbt to:

* Track lineage
* Apply freshness rules
* Validate schema consistency
* Reference them safely using `source()`

### 2. Staging Layer

Staging models standardize raw schemas:

* Rename columns
* Normalize types
* Apply basic filtering rules
* Enforce naming conventions

Examples:

* `stg_green_tripdata`
* `stg_yellow_tripdata`
* `stg_fhv_tripdata`

This layer ensures downstream transformations operate on clean, consistent structures.

### 3. Intermediate Layer

The intermediate layer combines and enriches trip-level data.

* `int_trips_unioned` merges Green and Yellow datasets.
* `int_trips` generates surrogate keys and enriches data with lookup tables.

Concepts learned:

* Surrogate key generation using `dbt_utils.generate_surrogate_key`
* Joining lookup tables
* The computational cost of window functions (e.g., deduplication using `ROW_NUMBER()`)

### 4. Mart Layer

The marts layer contains analytics-ready tables:

* `fct_trips`
* `dim_zones`
* `dim_vendors`
* `fct_monthly_zone_revenue`

These models are structured for business analysis and reporting.

---

## Key Concepts Learned

### 1. dbt Lineage and Dependency Resolution

When running:

```bash
dbt run --select int_trips_unioned
```

dbt automatically builds upstream dependencies required for that model. It does not build downstream models unless explicitly selected.

This reinforces:

* dbt constructs a Directed Acyclic Graph (DAG)
* Model execution respects dependency order
* Upstream models are built automatically
* Downstream models require explicit selection

Understanding lineage is critical for controlled execution in production environments.

---

### 2. Data Testing and Quality Enforcement

Generic tests such as:

* `unique`
* `not_null`
* `accepted_values`
* `relationships`

allow enforcing data constraints declaratively in `schema.yml`.

Example:

```yaml
accepted_values:
  values: [1, 2, 3, 4, 5]
```

If a new value appears (e.g., `6`), `dbt test` fails with a non-zero exit code.

Key learning:

* dbt does not auto-correct data
* Failing tests halt pipelines (unless severity is downgraded)
* Tests are first-class citizens in analytics engineering

---

### 3. Fact Table Aggregation

The `fct_monthly_zone_revenue` model aggregates trip-level data into monthly zone-level summaries.

Concepts applied:

* Grouping by business dimensions
* Summation of monetary metrics
* Month-based date extraction
* Filtering by service type
* Year-based analysis using `EXTRACT(year FROM revenue_month)`

This reflects real-world analytical use cases such as:

* Identifying top-performing zones
* Revenue analysis by service type
* Time-based performance metrics

---

### 4. Source Configuration in dbt

Raw tables must be declared explicitly in `sources.yml`.

Example:

```yaml
sources:
  - name: raw
    schema: prod
    tables:
      - name: green_tripdata
      - name: yellow_tripdata
      - name: fhv_tripdata
```

Without source declaration:

* dbt cannot compile models referencing raw data
* Lineage tracking breaks
* Freshness checks fail

This reinforces the separation between:

* Raw data (owned externally)
* Transformations (owned by analytics engineering)

---

### 5. Handling Large Data Volumes Locally

FHV data contains over 43 million records. During model execution, the following challenges emerged:

* Memory exhaustion during deduplication
* Heavy window function computation
* Hash aggregation limits in DuckDB

Key insights:

* Deduplication via window functions is computationally expensive
* Materializing large intermediate tables increases memory pressure
* Incremental models reduce recomputation cost
* Local engines behave differently from distributed warehouses

This exercise provided practical understanding of compute constraints in analytics workflows.

---

### 6. Incremental Models

`fct_trips` is implemented as an incremental model.

Conceptual understanding:

* Incremental models only process new data
* They reduce runtime and compute cost
* They are essential in large-scale pipelines

Even in local DuckDB, incremental patterns mirror real-world warehouse strategies.

---

### 7. Dimensional Modeling

The final models follow star schema principles:

* Fact tables contain measurable metrics (revenue, trip count)
* Dimension tables provide descriptive attributes (zones, vendors)

This separation supports:

* Efficient aggregation
* Business-friendly querying
* Scalable reporting design

---

## Business Questions Solved

Using the transformed models, we answered:

1. How dbt resolves model dependencies.
2. How data tests behave when unexpected values appear.
3. Total records in the revenue fact model.
4. The highest revenue zone for Green taxis in 2020.
5. Total Green taxi trips in October 2019.
6. Total FHV records after filtering null dispatching bases.

Each question required understanding different parts of the transformation stack.

---

## Technologies Used

* dbt Core
* DuckDB
* Python
* SQL
* NYC TLC public datasets

---

## Summary of Learning Outcomes

This module reinforced the following analytics engineering competencies:

* Building layered transformation pipelines
* Managing raw data sources declaratively
* Writing and enforcing data tests
* Understanding dbt lineage and execution behavior
* Designing fact and dimension models
* Handling large datasets within local compute constraints
* Debugging schema and source configuration issues
* Using SQL for business-level analytical queries

This project demonstrates practical application of analytics engineering principles in a reproducible local environment.

