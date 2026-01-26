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



