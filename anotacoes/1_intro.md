## Sumário
# Introdução à Engenharia de Dados
## Pipeline de dados
Um **_pipeline_ de dados** (**_data pipeline_**) é um conjunto de etapas que visam levar dados de uma ou mais origens a um ou mais destinos. Entre cada origem e destino, os dados passam por diversos processos (transformações e integrações) de modo a serem aplicáveis à finalidade.

![pipeline de dados](img/01_01.png)

## Arquitetura do projeto do curso

![architecture diagram](https://github.com/DataTalksClub/data-engineering-zoomcamp/raw/main/images/architecture/arch_1.jpg)

* [NYC TLC Dataset](https://github.com/DataTalksClub/data-engineering-zoomcamp/blob/main/dataset.md): Conjunto de dados de viagens de Táxi e Limusine de Nova Iorque. O dataset que será usado durante o curso.
* [Apache Spark](https://spark.apache.org/): Framework de código-aberto com o objetivo de processar grandes conjuntos de dados de forma paralela e distribuída.
* [Google BigQuery](https://cloud.google.com/products/bigquery/): _Data Warehouse_ sem servidor (_serverless_) que permite análises escalonáveis em _petabytes_ de dados.
* [Google Data Studio](https://marketingplatform.google.com/about/data-studio/): Ferramenta online para converter dados em _dashboards_ e relatórios informativos.
* [Apache Airflow](https://airflow.apache.org/): Plataforma de gerenciamento de fluxo de trabalho em código-aberto para _pipelines_ de Engenharia de Dados.
* [Apache Kafka](https://kafka.apache.org/): Plataforma de código-aberto para processamento de _streams_, com o objetivo de fornecer uma plataforma unificada, de alta capacidade e baixa latência para tratamento de dados em tempo real.

## Básico de Docker 
>"Docker é um conjunto de produtos de plataforma como serviço que usam virtualização de nível de sistema operacional para entregar software em pacotes chamados contêineres. Os contêineres são isolados uns dos outros e agrupam seus próprios softwares, bibliotecas e arquivos de configuração" -- [Wikipedia](https://pt.wikipedia.org/wiki/Docker_(software))

Cada **contêiner** é encapsulado e possui um sistema inteiro dentro de uma estrutura de diretório. Da perspectiva do _kernel Linux_, um contêiner é um processo com restrições: ao invés de executar um único arquivo binário, um contêiner executa uma **imagem**.

Uma **imagem** é um pacote com vários sistemas de arquivos em camadas sobrepostas, com todas as dependências necessárias para executar um processo.

Utilizar o Docker tem as seguintes vantagens:
* Facilidade de reprodução
* Testes locais
* Testes de integração (CI/CD)
* Rodar _pipelines_ em plataformas de _Cloud_ (AWS Batch, Kubernetes jobs)
* Apache Spark
* _Serverless_ (AWS Lambda, Google functions)

Os **contêineres** do Docker são voláteis (_stateless_ por natureza), ou seja, qualquer mudança dentro do contêiner **NÃO** será salvo quando o contêiner for encerrado e inicializado novamente. Para persistir os dados dentro dos contêineres é comum utilizarmos **volumes**.

Os **volumes** são diretórios externos ao contêiner, que são montados diretamente nele, e dessa forma não seguem o mesmo padrão de camadas. A principal função do volume é **persistir os dados**. Existem algumas particularidades entre os volumes e contêineres que valem a pena ser mencionadas:
* O volume é inicializado quando o contêiner é criado
* Caso ocorra de já haver dados no diretório em que o volume for montado, aqueles dados serão copiados para o volume
* Um volume pode ser reusado e compartilhado entre os contêineres
* Alterações em um volume são feitas diretamente no volume
* Alterações em um volume **não irão com a imagem** quando for feita cópia ou _snapshot_ de um contêiner
* Volumes **continuam a existir mesmo se o contêiner for deletado**

### [Video - Introduction to Docker](https://www.youtube.com/watch?v=EYNwNlOrpr0&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb)

Para o meu Linux Mint, instalei o Docker e o Docker Compose, ambos requisitos do curso, conforme abaixo:

```bash
# Cadastrei o repositório para o pacote do Docker e a chave
echo "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable" | sudo tee /etc/apt/sources.list.d/docker.list
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -

# Atualizei os repositórios do apt em busca de atualizações
sudo apt-get update

# Instalei as últimas versões do Docker Engine, Docker Compose e containerd
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Para corrigir os problemas com permissão para rodar o docker sem sudo
# Primeiramente adicionei um grupo chamado docker
sudo groupadd docker

# Adicionei meu usuário ao grupo
sudo usermod -aG docker $USER

# Alterei o grupo do docker.sock para o grupo docker
sudo chgrp docker /var/run/docker.sock

# E restartei o meu sistema para garantir que as modificações fizessem efeito
sudo reboot
```

Dentro do diretório da aula, foi criado um arquivo de teste chamado `pipeline.py`:

```python
import sys
import pandas as pd

print(sys.argv)
day = sys.argv[1]

print(f'job finished successfully for day={day}')
```

Ao rodar o script com `python pipeline.py <argumento>` teremos:
* `['pipeline.py', '<argumento>']`
* `job finished successfully for day=<argumento>`

Ainda no mesmo diretório, criei um arquivo chamado `Dockerfile`:

```dockerfile
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
```

Construí a imagem com:

```bash
# -t possibilita dar nome a uma imagem e associar uma tag a ela
# O nome da imagem é 'test'
# O nome da tag é 'pandas', se ela não fosse especificada seria 'latest'
docker build -t test:pandas .
```

Rodei o contêiner com um argumento no final afim de ser interpretado pelo script `pipeline.py`:

```bash
docker run -it test:pandas 2022-07-12
```

O resultado deve ser o esperado, com a lista de argumentos enviados ao script e ao final uma _string_ informando que a _job_ foi finalizada com sucesso e mostrando o argumento enviado ao rodar o contêiner.

Ao final, rodei o seguinte comando para remover de forma forçada todos os contêineres e imagens já criados:

```bash
# a flag -q traz somente os IDs
# a flag -a mostra todos os itens, até os parados/inativos

# CONTÊINERES
# 'docker ps' lista os contêineres
# 'docker rm -f' excluir forçadamente os contêineres selecionados
docker rm -f $(docker ps -qa)

# IMAGENS
# 'docker images' lista as imagens
# 'docker rmi -f' excluir forçadamente as imagens selecionadas
docker rmi -f $(docker images -qa)
```