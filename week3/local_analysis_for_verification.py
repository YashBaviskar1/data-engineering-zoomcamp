import duckdb
import pandas as pd
import requests
from io import BytesIO
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"
MONTHS = [f"{i:02d}" for i in range(1, 7)]

DB_FILE = "taxi.duckdb"
TABLE_NAME = "yellow_taxi_2024"

# -----------------------------
# DOWNLOAD PARQUET FILES
# -----------------------------
def download_parquet_files():
    files = []
    for month in MONTHS:
        file_path = DATA_DIR / f"yellow_tripdata_2024-{month}.parquet"
        if not file_path.exists():
            url = f"{BASE_URL}/yellow_tripdata_2024-{month}.parquet"
            print(f"Downloading {url}")
            r = requests.get(url)
            file_path.write_bytes(r.content)
        files.append(str(file_path))
    return files

# -----------------------------
# LOAD INTO DUCKDB
# -----------------------------
def load_into_duckdb(parquet_files):
    con = duckdb.connect(DB_FILE)

    con.execute(f"""
        CREATE OR REPLACE TABLE {TABLE_NAME} AS
        SELECT * FROM read_parquet({parquet_files})
    """)

    return con

# -----------------------------
# ANALYSIS QUERIES
# -----------------------------
def run_analysis(con):
    print("\n--- QUESTION 1: TOTAL RECORD COUNT ---")
    q1 = con.execute(f"SELECT COUNT(*) FROM {TABLE_NAME}").fetchone()[0]
    print(f"Total records: {q1:,}")

    print("\n--- QUESTION 4: ZERO FARE TRIPS ---")
    q4 = con.execute(f"""
        SELECT COUNT(*) 
        FROM {TABLE_NAME}
        WHERE fare_amount = 0
    """).fetchone()[0]
    print(f"Zero fare trips: {q4:,}")

    print("\n--- QUESTION 6: DISTINCT VENDOR IDS (DATE RANGE) ---")
    q6_df = con.execute(f"""
        SELECT DISTINCT VendorID
        FROM {TABLE_NAME}
        WHERE tpep_dropoff_datetime BETWEEN 
              '2024-03-01' AND '2024-03-15 23:59:59'
    """).df()
    print(q6_df)

    print("\n--- QUESTION 9: COUNT(*) EXPLANATION ---")
    print("""
COUNT(*) scans the entire table because:
- Every row must be counted
- DuckDB (like BigQuery) is columnar
- No column pruning is possible for COUNT(*)
    """)

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    parquet_files = download_parquet_files()
    con = load_into_duckdb(parquet_files)
    run_analysis(con)
