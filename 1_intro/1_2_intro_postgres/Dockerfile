FROM python:3.9.1

# Precisamos garantir que haja o wget para baixar o arquivo
RUN apt-get install wget

# psycopg2 é um adaptador de Postgres para Python e o sqlalchemy precisa dele
RUN pip install pandas sqlalchemy pyarrow psycopg2-binary

WORKDIR /app
COPY ingest_data.py ingest_data.py

# Cria o diretório para armazenar os arquivos de origem
RUN mkdir -p ./nyc_taxi_data

ENTRYPOINT [ "python", "ingest_data.py" ]