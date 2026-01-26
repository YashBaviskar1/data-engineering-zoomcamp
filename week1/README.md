# Data Engineering Zoomcamp week 1 



## Docker 


### What's the version of pip in the python:3.13 image? (1 point) 

Commands to execute to answer the question 
```bash 
docker -it --rm --entrypoint=bash python:3.13
root# pip --version 
```

output : `25.3`





###PSQL


Question : For the trips in November 2025, how many trips had a trip_distance of less than or equal to 1 mile?
 Query : 

```
SELECT COUNT(*) FROM public.yellow_taxi_data
WHERE '2025-11-01'::date <= lpep_pickup_datetime AND lpep_pickup_datetime < '2025-12-01'::date
AND trip_distance <= 1
```


Question : Question 5. Which was the pickup zone with the largest total_amount (sum of all trips) on November 18th, 2025? (1 point) 
Answer : 

need to sum all the total_amount for each pickup zone id and then arrange it in DSC (to get the pickup zone with largest amount and then JOIN that id with zones table 
```
SELECT
    z."Zone" AS pickup_zone,
    SUM(t.total_amount) AS total_revenue
FROM yellow_taxi_data t
JOIN zones z
    ON t."PULocationID" = z."LocationID"
WHERE t.lpep_pickup_datetime >= TIMESTAMP '2025-11-18'
  AND t.lpep_pickup_datetime <  TIMESTAMP '2025-11-19'
GROUP BY z."Zone"
ORDER BY total_revenue DESC
LIMIT 10;
```



Question 6 : For the passengers picked up in the zone named "East Harlem North" in November 2025, which was the drop off zone that had the largest tip? (1 point) 

yellow_taxi_data
→ filter by pickup zone = East Harlem North
→ filter by November 2025
→ group by DROP-OFF zone
→ find the largest tip
→ return that drop-off zone


```
SELECT
    zdo."Zone" AS dropoff_zone,
    MAX(t.tip_amount) AS max_tip
FROM yellow_taxi_data t
JOIN zones zpu
    ON t."PULocationID" = zpu."LocationID"
JOIN zones zdo
    ON t."DOLocationID" = zdo."LocationID"
WHERE zpu."Zone" = 'East Harlem North'
  AND t.lpep_pickup_datetime >= TIMESTAMP '2025-11-01'
  AND t.lpep_pickup_datetime <  TIMESTAMP '2025-12-01'
GROUP BY zdo."Zone"
ORDER BY max_tip DESC
LIMIT 1;
```



