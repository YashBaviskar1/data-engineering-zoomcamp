import dlt
import requests


@dlt.resource(name="trips", write_disposition="replace")
def taxi_source():
    """Fetch NYC taxi trip data from the REST API.
    
    The API returns paginated JSON data with 1,000 records per page.
    Pagination stops when an empty page is returned.
    """
    page = 1
    while True:
        response = requests.get(
            f"https://us-central1-dlthub-analytics.cloudfunctions.net/data_engineering_zoomcamp_api?page={page}"
        )
        response.raise_for_status()
        data = response.json()
        
        # Stop when we get an empty page
        if not data:
            break
        
        # Yield all records from this page
        for record in data:
            yield record
        
        page += 1


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="taxi_pipeline",
        destination="duckdb",
        dataset_name="taxi_data",
        progress="log"
    )
    load_info = pipeline.run(taxi_source())
    print(load_info)