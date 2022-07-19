#!/usr/bin/env python
# coding: utf-8

# ## Ingesting NY Taxi Data to Postgres 

# Itens relacionados:
# * [Notas](../../anotacoes/1_intro.md)
# * [Vídeo 1](https://www.youtube.com/watch?v=2JM-ziJt0WI&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=5)
# * [Vídeo 2](https://www.youtube.com/watch?v=3IkfkTwqHx4&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=6)

# ### Instalação de requisitos

# No meu computador eu não possuía o Anaconda para Python, então não tinha o Jupyter Notebook do pacote.
# Utilizei o [`pyenv`](https://github.com/pyenv/pyenv) para Linux e com ele já veio o [`pyenv-virtualenv`](https://github.com/pyenv/pyenv-virtualenv) que permite gerenciar ambientes virtuais para Python em sistemas baseados em UNIX. É uma espécie de _wrapper_, que centraliza os ambientes virtuais em um diretório raíz.
# Após instalar o `pyenv` com o [`pyenv-installer`](https://github.com/pyenv/pyenv-installer), criei um ambiente virtual e instalei os seguintes pacotes com o `pip`:

# `pip install ipykernel pandas sqlalchemy pyarrow psycopg2-binary`

# * `ipykernel`: necessário para rodar os arquivos Jupyter Notebook
# * `pandas`: biblioteca que fornece ferramentas para análise e manipulação de dados
# * `sqlalchemy`: biblioteca com ferramentas e ORM (_Object Relational Mapper_) para utilização de SQL aliado ao Python
# * `pyarrow`: plataforma de desenvolvimento para análises _in-memory_
# * `psycopg2-binary`: adaptador Python para PostgreSQL

# ### Iniciando o trabalho de investigação dos dados

# In[1]:


import pandas as pd
# pd.__version__


# In[2]:


import pyarrow.csv as csv
import pyarrow.parquet as pq


# O arquivo com os dados é muito grande e o `pandas` não é capaz de lidar com ele da melhor maneira por questões de memória RAM. 
# No curso os dados vêm em CSV, porém em julho/2022 a extensão no site mudou para PARQUET. Para seguir os passos apresentados no curso, foi feita a conversão de PARQUET para CSV usando o `pyarrow`:

# In[3]:


table = pq.read_table('./nyc_taxi_data/yellow_tripdata_2021-01.parquet')
options = csv.WriteOptions(include_header=True)
csv.write_csv(
    table, 
    './nyc_taxi_data/yellow_tripdata_2021-01.csv', 
    options)


# O arquivo CSV vai ser usado posteriormente na hora de inserir os dados no banco de dados no `PostgreSQL`. 
# Optei por criar o `DataFrame` do `pandas` utilizando a `table` obtida pela leitura do arquivo em PARQUET porque ao fazer isso, garanti o tipo de dados `TIMESTAMP` de maneira direta. No curso, ao ler do CSV o tipo das colunas `TIMESTAMP` vão para `TEXT` e ele faz a conversão de forma manual toda vez que lê do arquivo de origem.

# Por ora, precisaremos apenas das 100 primeiras linhas:

# In[4]:


df = table.to_pandas().head(n=100)
df


# Vamos agora verificar o **_schema_** necessário. O _schema_ é uma estrutura lógica de dados que, no `PostgreSQL` serve como coleção de tabelas, _views_, funções, restrições (_constraints_), índices, etc. No nosso caso, vamos ver como vai ser a criação da tabela para inserir os dados. O `pandas` consegue nos dar o **DDL** (_Data Definition Language_) em SQL com as instruções necessárias para criar a tabela:

# In[5]:


print(pd.io.sql.get_schema(df, name='yellow_taxi_data'))


# **IMPORTANTE: Precisamos "printar" para que o resultado venha como uma instrução SQL.** 

# ### Criando a tabela no banco de dados

# Apesar de termos as instruções DDL, tudo não passou de uma verificação de qual será a instrução passado para o `PostgreSQL`, não foi feita a criação e nem mesmo a conexão com o banco de dados ainda. Iremos utilizar o `sqlalchemy` para isso:

# In[6]:


from sqlalchemy import create_engine


# Um **engine** especifica os detalhes do banco de dados em uma **URI** (_Uniform Resource Identifier_):
# `database://user:password@host:port/database_name`

# In[7]:


engine = create_engine('postgresql://root:root@localhost:5432/ny_taxi')


# In[8]:


engine.connect()


# **IMPORTANTE: Só vamos conseguir se conectar no banco de dados se o contêiner do `PostgreSQL` já foi criado no `Docker` e estiver rodando.**

# Passando o valor da nossa **URI de conexão** para o argumento `con=` conseguimos trazer o DDL específico para o `PostgreSQL`, com todos os tipos de dados suportados e automaticamente reconhecidos.

# In[9]:


print(pd.io.sql.get_schema(df, name='yellow_taxi_data', con=engine))


# Agora iremos criar um **iterador** para nos permitir ler o CSV em blocos de 100.000 linhas e enviá-los ao banco de dados, para evitar incorrer em erros ao tentar inserir muitos registros de uma só vez.

# In[10]:


df_iter = pd.read_csv(
    './nyc_taxi_data/yellow_tripdata_2021-01.csv',
    iterator=True,
    chunksize=100000)


# Como se trata de um iterador, conseguimos usar a função `next()` para acessar seu valor.

# In[11]:


df = next(df_iter)
df


# Como lemos do CSV, ao vermos o tipo de dados das colunas através do comando do `pandas` que gera o _schema_, podemos perceber aquele problema com as colunas de tipo `TIMESTAMP`:

# In[12]:


print(pd.io.sql.get_schema(df, name='yellow_taxi_data'))


# Portanto, precisamos converter manualmente essas colunas:

# In[13]:


df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
print(pd.io.sql.get_schema(df, name='yellow_taxi_data'))


# Finalmente vamos criar a tabela no banco de dados. Com o comando `df.head(n=0)` nós conseguimos somente os nomes das colunas. Nós usaremos isso para criar a instrução SQL que vai gerar a tabela.

# In[14]:


df.head(n=0).to_sql(
    name='yellow_taxi_data',
    con=engine,
    if_exists='replace'
)


# Agora, usando o comando `read_sql` do `pandas` e a _query_ abaixo, conseguimos ver as tabelas criadas no banco de dados.

# In[15]:


query = """
SELECT *
FROM pg_catalog.pg_tables
WHERE schemaname != 'pg_catalog'
AND schemaname != 'information_schema';
"""
pd.read_sql(query, con=engine)


# Conseguimos ver também informações sobre a tabela criada com a seguinte _query_. Assim, constatamos que os tipos de dados que obtivemos ao consultar o _schema_ que iria ser criado pelo `pandas.io.sql.get_schema()` ao inserir os dados no `PostgreSQL` se concretizaram através do método `pd.DataFrame.to_sql()`.
# 

# In[16]:


query_describe = """
SELECT * FROM information_schema.columns
WHERE table_name = 'yellow_taxi_data';
"""
pd.read_sql(query_describe, con=engine)


# Vamos incluir o bloco de 100.000 registros no banco de dados para verificar o tempo que levará para a inserção.

# In[17]:


get_ipython().run_line_magic('time', "df.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')")


# Vendo a quantidade de dados inseridos na tabela no `PostgreSQL`, que deve bater com a quantidade da origem (100.000 registros).

# In[18]:


pd.read_sql(sql="SELECT COUNT(1) FROM yellow_taxi_data;", con=engine)


# Apesar de não ser o melhor código possível, é criado um _loop_ para iterar sobre o arquivo CSV, extraindo blocos de 100.000 registros por vez e os armazenando em `DataFrames` na memória, permitindo a inserção aos poucos na tabela do `PostgreSQL`.

# In[19]:


from time import time

while True:
    try:
        t_start = time()
        df = next(df_iter)

        df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
        df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)

        df.to_sql(name='yellow_taxi_data', con=engine, if_exists='append')

        t_end = time()

        print(f'Inserido outro bloco, levou {(t_end - t_start):3f} segundos')
    except StopIteration:
        print('Inserção completa')
        break


# Checando se na tabela consta a mesma quantidade de registros que no arquivo de origem.

# #### Contagem na ORIGEM

# In[20]:


len(table)


# #### Contagem no DESTINO

# In[21]:


pd.read_sql(sql="SELECT COUNT(1) FROM yellow_taxi_data;", con=engine)

