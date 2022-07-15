# Imagem do Docker que vai servir de base
FROM python:3.9

# Prepara nossa imagem para instalar os pré-requisitos direto na instanciação do contêiner
RUN pip install pandas

# Configura o Working Directory dentro do contêiner
WORKDIR /app

# Copia o script presente na máquina, no mesmo diretório deste Dockerfile para o Working Dir do contêiner
# 1o nome é na origem (máquina local)
# 2o nome é no destino (contêiner)
COPY pipeline.py pipeline.py

# Define o que fazer quando o contêiner rodar
ENTRYPOINT ["python", "pipeline.py"]