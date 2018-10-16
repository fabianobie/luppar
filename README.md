
# Luppar

#### Luppar: Sistema de Recuperação de Informação dotado de Análise de Contexto Local Baseada em Modelo Semântico Distribucional

> Uma ferramenta de Recuperação de Informação com código fonte aberto que utiliza um modelo semântico distribucional local associado a cada corpus. O sistema realiza expansão automática de consulta utilizando uma combinação de modelo semântico distribucional e análise de contexto local e suporta realimentação de relevância. O desempenho do sistema foi avaliado em bases de dados de diferentes domínios e apresentou resultados satisfatórios frente aqueles publicados na literatura.

#### [www.luppar.com](http://luppar.com "www.luppar.com")

## Funcionalidades:

- Um Framework de Recuperação de Informação
- Motor de Busca Web simplificado
- Coleção de referência
- Expansão de Consulta:
	1. Modelo Semântico Distribucional
	2. Análise de Contexto Local
	3. Wordnet
- Modelo de Busca:
	1. Booleano
	2. Vetorial
	3. Probabilístico
- Métricas de Avaliação em RI



## Pré-requisitos:

#### GCC
    $ sudo apt-get install gcc

#### PYTHON
Instalar python 3.6 e Pip3
 ```bash
    $ sudo apt install python3
    $ sudo apt install python3-pip
```

#### MYSQL
Instalar mysql sever
 ```bash
    $ sudo apt install mysql-server
```
Configurar mysql e criar o *schema* 'luppar'

    $ mysql -u root -p
    > CREATE SCHEMA `luppar` DEFAULT CHARACTER SET utf8 ;

#### GIT
Instalar git
 ```bash
$ sudo apt install git
```

## Instalação Luppar

```shell
$ cd
$ git clone https://github.com/usnistgov/trec_eval.git
$ cd trec_eval
$ make
$ sudo make install
$ cd
```

```shell
$ cd
$ git clone https://github.com/fabianobie/luppar.git
$ cd luppar
$ pip3 install -r requirements.txt
$ cp .env.example .env
$ vim .env
```
adicionar no arquivo .env as seguintes configurações:
```json
DEBUG=True
SECRET_KEY=ha72y3h2h423hdh32hr23y9rhhf43ry3h4f7h3
DATABASE_NAME=luppar
DATABASE_URL=localhost
DATABASE_USER=root
DATABASE_PASS=admin
DATABASE_PORT=3306
```

```bash
$ python3 manage.py migrate
$ python3 manage.py createsuperuser --username=admin --email=admin@example.com
$ python3 manage.py loaddata luppar_dump.json
$ python3  download_data.py
$ python3 manage.py runserver
```

Aguarde alguns minutos para indexação e então acesse
`http://localhost:8000` e `http://localhost:8000/admin`
