
***

```markdown
# Data Engineering Zoomcamp: Module 7 Homework (Streaming with Redpanda & PyFlink)

This repository contains the solutions and explanations for the Module 7 Homework of the Data Engineering Zoomcamp. The project demonstrates real-time stream processing using **Redpanda** (a Kafka-compatible broker), **PostgreSQL**, and **Apache Flink** (PyFlink).

## 🛠️ Setup & Prerequisites
The infrastructure is orchestrated using Docker Compose and includes:
- **Redpanda:** Message broker running on `localhost:9092` (external) and `redpanda:29092` (internal).
- **Flink JobManager & TaskManager:** Stream processing engine (`localhost:8081`).
- **PostgreSQL:** Sink database for aggregated results (`localhost:5432`).

---

## 🚨 Critical Data Prep Note: The "Poison Pill"
Before executing the Flink jobs, the Green Taxi dataset required specific preprocessing in the Python producer. 
1. **Datetime Conversion:** Flink's SQL expects strings for timestamps, so `lpep_pickup_datetime` and `lpep_dropoff_datetime` were cast to strings.
2. **Handling `NaN`:** The `passenger_count` column contained `NaN` (Not a Number) values. Standard Python `json.dumps()` allows `NaN`, but Flink's strict JSON parser will crash immediately upon reading it. 
**Fix:** We applied `df.fillna(0)` before serializing the data to Kafka.

---

## 📝 Solutions & Explanations

### Question 1: Redpanda Version
**Command:**
```bash
docker exec -it workshop-redpanda-1 rpk version
```
**Explanation:** `rpk` is the Redpanda command-line interface. Executing this inside the container reveals the exact version of the broker running. Based on the `docker-compose.yml`, this is **v25.3.9**.

---

### Question 2: Sending Data to Redpanda
**Objective:** Create a Kafka topic `green-trips` and write a Python producer to send filtered Parquet data to it.

**Command to create topic:**
```bash
docker exec -it workshop-redpanda-1 rpk topic create green-trips
```

**Producer Code (`src/producers/green_producer.py`):**
```python
import json
from time import time
import pandas as pd
from kafka import KafkaProducer

url = "[https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-10.parquet](https://d37ci6vzurychx.cloudfront.net/trip-data/green_tripdata_2025-10.parquet)"
columns = ["lpep_pickup_datetime", "lpep_dropoff_datetime", "PULocationID", "DOLocationID", "passenger_count", "trip_distance", "tip_amount", "total_amount"]

df = pd.read_parquet(url, columns=columns)
df["lpep_pickup_datetime"] = df["lpep_pickup_datetime"].astype(str)
df["lpep_dropoff_datetime"] = df["lpep_dropoff_datetime"].astype(str)
df = df.fillna(0) # CRITICAL: Prevents Flink JSON parsing errors

producer = KafkaProducer(
    bootstrap_servers=["localhost:9092"],
    value_serializer=lambda data: json.dumps(data).encode("utf-8")
)

t0 = time()
for _, row in df.iterrows():
    producer.send("green-trips", value=row.to_dict())
producer.flush()
print(f"took {(time() - t0):.2f} seconds")
```
**Result:** Processing took roughly **10-20 seconds** (depending on hardware). 
**Why it's done:** The producer acts as our simulated real-time data ingestion point. `producer.flush()` ensures all asynchronous messages are fully transmitted before stopping the timer.

---

### Question 3: Consumer - Trip Distance
**Objective:** Count how many trips have a `trip_distance` > 5.0 km using a Python Kafka Consumer.

**Consumer Code (`src/consumers/green_consumer.py`):**
```python
import json
from kafka import KafkaConsumer

consumer = KafkaConsumer(
    'green-trips',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    consumer_timeout_ms=5000 # Stop loop after 5 seconds of inactivity
)

count = sum(1 for msg in consumer if float(msg.value.get('trip_distance', 0)) > 5.0)
print(f"Trips > 5km: {count}")
```
**Why it's done:** - `auto_offset_reset='earliest'` ensures we read the topic from the very beginning.
- `consumer_timeout_ms=5000` is crucial. Unlike batch processing, Kafka streams are infinite. Without a timeout, the `for msg in consumer` loop would hang forever waiting for new data.

---

### Core Flink Architecture Notes (Applies to Q4, Q5, Q6)
For all Flink jobs, we used specific configurations:
1. `env.set_parallelism(1)`: Since our Kafka topic only has 1 partition, setting parallelism to >1 causes idle consumer subtasks. Idle subtasks prevent the Watermark from advancing, which means windows never close and data is never written to PostgreSQL.
2. `PRIMARY KEY (...) NOT ENFORCED`: In our Sink DDLs, defining a Primary Key allows Flink's JDBC connector to perform **Upserts** (Updates/Inserts). If a late-arriving event falls into an already-processed window, Flink can update the existing row in Postgres rather than appending a duplicate.
3. `WATERMARK FOR event_timestamp`: Tells Flink to wait 5 seconds for late-arriving data before publishing a window's results.

---

### Question 4: Tumbling Window - Pickup Location
**Objective:** Find the `PULocationID` with the most trips in a single 5-minute fixed window.

**SQL Logic (`q4_job.py`):**
```sql
INSERT INTO trips_5min_tumbling
SELECT
    window_start,
    PULocationID,
    COUNT(*) AS num_trips
FROM TABLE(
    TUMBLE(TABLE green_trips, DESCRIPTOR(event_timestamp), INTERVAL '5' MINUTE)
)
GROUP BY window_start, PULocationID
```
**Result:** `PULocationID` **74**
**Why it's done:** `TUMBLE` creates fixed, non-overlapping windows (e.g., 12:00-12:05, 12:05-12:10). This is useful for periodic reporting where time boundaries are strict.

---

### Question 5: Session Window - Longest Streak
**Objective:** Group events by `PULocationID` into "sessions" based on a 5-minute inactivity gap. Find the longest session.

**SQL Logic (`q5_job.py`):**
```sql
INSERT INTO sink_sessions
SELECT
    PULocationID,
    SESSION_START(event_timestamp, INTERVAL '5' MINUTE) as window_start,
    SESSION_END(event_timestamp, INTERVAL '5' MINUTE) as window_end,
    COUNT(*) as num_trips
FROM source_trips
GROUP BY
    PULocationID,
    SESSION(event_timestamp, INTERVAL '5' MINUTE)
```
**Result:** **81** trips
**Why it's done:** Unlike tumbling windows, `SESSION` windows are dynamic. The window stays open as long as taxis keep picking up passengers at a specific location within 5 minutes of each other. Once 5 minutes pass with *no* pickups at that location, the window closes. This is excellent for measuring behavioral streaks.

---

### Question 6: Tumbling Window - Largest Tip
**Objective:** Calculate the total tip amount per hour across all locations to find the most lucrative hour.

**SQL Logic (`q6_job.py`):**
```sql
INSERT INTO sink_tips
SELECT
    window_start,
    SUM(tip_amount) as total_tip
FROM TABLE(
    TUMBLE(TABLE source_trips, DESCRIPTOR(event_timestamp), INTERVAL '1' HOUR)
)
GROUP BY window_start
```
**Why it's done:** By using an `INTERVAL '1' HOUR` tumbling window and omitting the location ID from the `GROUP BY` clause, we effectively aggregate the sum of all tips globally across the entire city for that specific hour.

```

