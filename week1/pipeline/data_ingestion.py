#!/usr/bin/env python
# coding: utf-8

# In[9]:
import click
from sqlalchemy import create_engine
import pandas as pd
@click.command()
@click.option('--pg-user', default='postgres', help='PostgreSQL user')
@click.option('--pg-pass', default='postgres', help='PostgreSQL password')
@click.option('--pg-host', default='localhost', help='PostgreSQL host')
@click.option('--pg-port', default=5433, type=int, help='PostgreSQL port')
@click.option('--pg-db', default='ny_taxi', help='PostgreSQL database name')
@click.option('--target-table', default='yellow_taxi_data', help='Target table name')
@click.option('--database', default='taxi_zone_lookup.csv', help='dataset name, in csv format')
def run(pg_user, pg_pass, pg_host, pg_port, pg_db, target_table, database):

#get_ipython().system('pip list')
    df = pd.read_csv(database)
    df.head()
    df.columns
    df.dtypes
    df.shape
    engine = create_engine(f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}")
    print(engine)
    print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))
    df.head(n=0).to_sql(name='yellow_taxi_data', con=engine, if_exists='replace')
    # ## Since the size of data is only 200 x 4, no need to chunk and iter it and can be directly appended 
    # 
    # ### Note : will improve this part later

    # In[23]:
    df.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')


    # In[ ]:


if __name__ == '__main__':
    run()


