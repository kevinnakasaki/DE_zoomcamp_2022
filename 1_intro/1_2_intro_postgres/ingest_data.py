import argparse
import os
from time import time
import pandas as pd
import pyarrow.csv as csv
import pyarrow.parquet as pq
from sqlalchemy import create_engine


def convert_parquet_to_csv(in_path: str, out_path: str) -> None:

    table = pq.read_table(in_path)
    options = csv.WriteOptions(include_header=True)
    csv.write_csv(
        table, 
        out_path, 
        options)


def main(params):

    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    url = params.url
    data_dir = './nyc_taxi_data'
    parquet_file = f'{data_dir}/yellow_tripdata_2021-01.parquet'
    csv_file = f'{data_dir}/yellow_tripdata_2021-01.csv'


    # Baixando o arquivo PARQUET
    os.system(f'wget {url} -O {parquet_file}')

    convert_parquet_to_csv(
        in_path=f'{parquet_file}',
        out_path=f'{csv_file}')

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')

    df_iter = pd.read_csv(f'{csv_file}', iterator=True, chunksize=100000)
    df = next(df_iter)

    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

    df.head(n=0).to_sql(name=table_name, con=engine, if_exists='replace')

    df.to_sql(name=table_name, con=engine, if_exists='append')

    while True:
        try:
            t_start = time()

            df = next(df_iter)

            df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
            df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

            df.to_sql(name=table_name, con=engine, if_exists='append')

            t_end = time()

            print(f'Inserido outro bloco, levou {(t_end - t_start):3f} segundos')
        except StopIteration:
            print('Inserção completa')
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Ingesting data to Postgres')

    parser.add_argument('--user', help='username for Postgres')
    parser.add_argument('--password', help='password for Postgres')
    parser.add_argument('--host', help='host for Postgres')
    parser.add_argument('--port', help='port for Postgres')
    parser.add_argument('--db', help='database name in Postgres')
    parser.add_argument('--table_name', help='name of the table where we will write the results to')
    parser.add_argument('--url', help='url to download the file containing the data')

    args = parser.parse_args()

    main(args)