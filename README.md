# 📚 Books API — Flask Web Scraper e API com Machine Learning

Este projeto consiste em uma aplicação **Python Flask** que realiza **web scraping** do site [Books to Scrape](https://books.toscrape.com/), salva os dados localmente em `.csv`, armazena-os em um banco **PostgreSQL** e disponibiliza uma **API RESTful documentada com Swagger** para consultas, estatísticas e endpoints de machine learning. Também possui JWT e autenticação, refresh de tokens, senhas criptografadas, manipulaçào de cache e proteção contra ataques de sobrecarga nos endpoints.

## Deploy do Projeto no render

[Deploy no render](https://fiap-sp30.onrender.com/) 

[Vídeo de apresentação](https://www.youtube.com/watch?v=4SuFxibIm4I)

---

## Arquitetura

Infraestrutura : Render 
Banco de dados : PostgreSQL como serviço no Render
Api            : Flask como serviço no render

---

## 🎯 Modelo inicial 

<img src="https://github.com/jemaldonado/fiap/blob/main/arq.PNG" alt="Alt text" width="100%">

## 🧩 Estrutura do Projeto

```

app.py                # Inicialização principal da aplicação Flask
config.py             # Configurações da aplicação e do Swagger
database.py           # Configuração da conexão com o banco PostgreSQL
models.py             # Definição das classes User e Book
routes/
├── auth.py           # Rotas de autenticação e JWT
└── books.py          # Rotas de livros, estatísticas e ML
scraper/
├── books_scraper.py  # Script de scraping que coleta os dados do site
└── data/
    └── books.csv     # Arquivo CSV gerado com os dados coletados
requirements.txt       # Dependências do projeto
```

---

## 📦 Layout do CSV

O script de scraping (`scraper/books_scraper.py`) gera um arquivo `books.csv` dentro da pasta `api/scraper/data/`, com o seguinte layout:

```
title
category
price
price_excl_tax
price_incl_tax
rating
upc
availability
description
image_url
book_url
number_of_reviews
product_type
tax
```

Esses dados são carregados para o banco de dados via a rota protegida:

```
POST /api/v1/scraping/trigger
```

---

## ⚙️ Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seuusuario/books-flask-api.git
cd books-flask-api
```

### 2. Crie e ative o ambiente virtual

```bash
python -m venv venv
source venv/bin/activate     # Linux/Mac
venv\Scripts\activate        # Windows
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Configure o banco de dados

Crie um arquivo .env e coloco suas chaves para cripgrafia e url de banco de dados.

```python
SQLALCHEMY_DATABASE_URI = "postgresql://usuario:senha@localhost:5432/booksdb"
```

### 5. Execute o scraper

Antes de rodar a API, é necessário gerar o CSV com os dados dos livros:

```bash
python scraper/books_scraper.py
```

Isso criará `api/scraper/data/books.csv`.

### 6. Inicialize a API Flask

```bash
python app.py
```

A aplicação estará disponível em:

👉 **http://localhost:5000/apidocs**

---

## 🔐 Autenticação e JWT

A API utiliza **JWT (JSON Web Token)** para autenticação.

| Método | Endpoint     | Descrição                      |
|:-------|:--------------|:------------------------------|
| POST   | /register     | Registra um novo usuário       |
| POST   | /login        | Retorna tokens access e refresh|
| POST   | /refresh      | Gera novo access token         |
| GET    | /protected    | Rota protegida para teste      |

---

## 📚 Rotas de Livros

| Método | Endpoint | Descrição |
|:-------|:----------|:-----------|
| POST | /api/v1/scraping/trigger | Carrega os dados do `books.csv` para o banco |
| GET | /api/v1/books | Lista paginada de livros |
| GET | /api/v1/books/<id> | Detalhes de um livro |
| GET | /api/v1/search | Busca por título ou categoria |
| GET | /api/v1/categories | Lista categorias únicas |
| GET | /api/v1/price-range | Filtra por faixa de preço |
| GET | /api/v1/top-rated | Retorna livros com maiores ratings |
| POST | /api/v1/health | verifica se o banco de dados está aitvo e respondendo querys |

---

## 📊 Estatísticas

| Método | Endpoint | Descrição |
|:-------|:----------|:-----------|
| GET | /api/v1/stats/overview | Total de livros, preço médio, distribuição de ratings |
| GET | /api/v1/stats/categories | Estatísticas detalhadas por categoria |

---

## ⚡ Cache

| Método | Endpoint | Descrição |
|:-------|:----------|:-----------|
| POST | /api/v1/cache | limpa cache da aplicação |

---

## 🤖 Machine Learning Endpoints

| Método | Endpoint | Descrição |
|:-------|:----------|:-----------|
| GET | /api/v1/ml/features | Retorna features processadas (tokenização e encoding) |
| GET | /api/v1/ml/training-data | Retorna amostra formatada para treino/teste |
| POST | /api/v1/ml/predictions | Recebe dados e retorna previsão de preço (simulada) |

### Exemplo de requisição de previsão

```json
POST /api/v1/ml/predictions
{
  "category": "Travel",
  "rating": 3,
  "availability": 5,
  "in_stock": 1,
  "number_of_reviews": 0,
  "title_processed": ["science", "fiction"],
  "description_processed": ["a", "thrilling", "novel"]
}
```

### Resposta esperada

```json
{
  "predicted_price": 27.45,
  "input": {
    "category": "Travel",
    "rating": 3,
    "availability": 5,
    "in_stock": 1,
    "number_of_reviews": 0,
    "title_processed": ["science", "fiction"],
    "description_processed": ["a", "thrilling", "novel"]
  }
}
```

---

## 🧠 Tecnologias Utilizadas

⚙️ Bibliotecas Principais Utilizadas na API

A aplicação Flask foi construída com foco em segurança, desempenho e escalabilidade, utilizando diversas bibliotecas que fortalecem a autenticação, controle de acesso, cache e integridade dos dados.

🧩 Flask-Caching
from flask_caching import Cache

📘 Descrição

O Flask-Caching é utilizado para armazenar resultados temporários de consultas e cálculos, melhorando o desempenho da API e reduzindo o tempo de resposta.

💡 Exemplo de uso:

Na rota /cache, o cache é limpo manualmente:

@books_bp.route('/cache', methods=['POST'])
def clear_cache():
    cache.clear()
    return jsonify({"msg": "Cache limpo com sucesso"}), 200


Isso garante que dados obsoletos sejam descartados de forma controlada.

✅ Benefício

Diminui carga no banco de dados.

Aumenta performance em endpoints acessados frequentemente.

Permite controle fino sobre invalidação de cache.

🔐 Flask-JWT-Extended
from flask_jwt_extended import (
    JWTManager, create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)

📘 Descrição

Biblioteca essencial para autenticação e autorização baseada em JWT (JSON Web Tokens).
Permite proteger endpoints e garantir que apenas usuários autenticados acessem determinados recursos.

💡 Exemplo de uso:

Na rota de login:

@auth_bp.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200


Na rota protegida:

@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    return jsonify({"msg": f"Usuário com ID {current_user_id} acessou a rota protegida."}), 200

✅ Benefício

Tokens seguros e independentes de sessão.

Permite refresh tokens para renovação sem reautenticação.

Facilita integração com frontends modernos (React, Vue, etc).

🛡️ Flask-Limiter
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

📘 Descrição

O Flask-Limiter protege a API contra ataques de sobrecarga (DoS) e uso abusivo, limitando o número de requisições por IP em intervalos definidos.

💡 Exemplo de uso:
@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per 10 minutes", override_defaults=True)
def register_user():
    ...


Na rota /protected, o uso é ainda mais restritivo:

@auth_bp.route('/protected', methods=['GET'])
@limiter.limit("1 per 1 minutes", override_defaults=True)
@jwt_required()
def protected():
    ...

✅ Benefício

Evita spam e tentativas de brute-force.

Melhora a estabilidade da aplicação sob alta demanda.

Pode aplicar limites globais, por rota ou por IP.

🔑 Werkzeug Security
from werkzeug.security import generate_password_hash, check_password_hash

📘 Descrição

Fornece métodos para criptografia e validação segura de senhas, utilizando algoritmos modernos como PBKDF2 e SHA-256.

💡 Exemplo de uso:

Na rota /register:

hashed_password = generate_password_hash(
    data['password'], method='pbkdf2:sha256', salt_length=16
)


E na rota /login:

if user and check_password_hash(user.password, data['password']):
    ...

✅ Benefício

Evita armazenamento de senhas em texto puro.

Adiciona “sal” automaticamente, dificultando ataques de dicionário.

Cumpre boas práticas de segurança para aplicações web.

🌐 Requests
import requests

📘 Descrição

Biblioteca utilizada para consumir páginas e APIs externas de forma simples, ideal para tarefas de web scraping e integração com serviços de terceiros.

💡 Exemplo de uso:

No módulo scraper (não mostrado aqui), é usada para obter páginas HTML do site Books to Scrape:

response = requests.get("https://books.toscrape.com/")

✅ Benefício

Simples e poderosa para fazer requisições HTTP.

Suporte nativo a cookies, headers e autenticação.

Amplamente utilizada em pipelines de dados e APIs.

🕸️ BeautifulSoup
from bs4 import BeautifulSoup

📘 Descrição

Usada junto com requests para extrair dados estruturados de páginas HTML (ex: títulos, preços, descrições, categorias).

💡 Exemplo de uso:
soup = BeautifulSoup(response.text, 'html.parser')
titles = [book.h3.a['title'] for book in soup.select('.product_pod')]

✅ Benefício

Facilita navegação no DOM e extração de dados.

Compatível com seletores CSS e expressões regulares.

Ideal para web scraping e coleta de dados automatizada.

🧠 NLTK (Natural Language Toolkit)
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

📘 Descrição

O NLTK é uma das principais bibliotecas de Processamento de Linguagem Natural (NLP).
Na aplicação, é usada para tokenizar e limpar textos, removendo stopwords e preparando dados para aprendizado de máquina.

💡 Exemplo de uso:
stop_words = set(stopwords.words())
def tokenize_and_remove_stopwords(text):
    tokens = word_tokenize(text.lower())
    return [word for word in tokens if word.isalnum() and word not in stop_words]

✅ Benefício

Prepara textos para modelos de ML e análise semântica.

Suporta múltiplos idiomas.

Integra-se facilmente com pandas e scikit-learn.

📊 Pandas & Scikit-Learn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

📘 Descrição

Essenciais para manipulação de dados tabulares e preparação de features para aprendizado de máquina.

💡 Exemplo de uso:

Na rota /ml/features:

preprocessor = ColumnTransformer(
    transformers=[('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), ['category'])],
    remainder='passthrough'
)
processed_data = preprocessor.fit_transform(df_processed)


E na rota /ml/training-data:

X_train, X_test, y_train, y_test = train_test_split(
    X, y, train_size=train_split, random_state=random_state
)

✅ Benefício

Facilita engenharia de features e codificação de variáveis.

Suporte completo a splits reprodutíveis e pipelines ML.

Cria base sólida para futuras integrações com modelos preditivos.

🧾 Resumo Final
Biblioteca	Função Principal	Exemplo de Uso
Flask-Caching	Cache e performance	/cache limpa cache da aplicação
Flask-JWT-Extended	Autenticação e autorização via JWT	/login, /protected, /refresh
Flask-Limiter	Proteção contra ataques de sobrecarga	/register, /protected
Werkzeug Security	Criptografia segura de senhas	/register e /login
Requests + BeautifulSoup	Web scraping e coleta de dados	Coleta de livros no BooksToScrape
NLTK	Processamento de linguagem natural	Tokenização e remoção de stopwords
Pandas + Scikit-Learn	Pré-processamento e ML	/ml/features, /ml/training-data

---

## 🧰 Endpoints Utilitários

| Método | Endpoint | Descrição |
|:-------|:----------|:-----------|
| GET | /api/v1/health | Verifica se o banco está acessível |
| POST | /api/v1/cache | Limpa o cache da aplicação |

---

## 🧑‍💻 Autor

**Juan Eduardo Maldonado**

---

## 🏗️ Futuras Melhorias

- Previsão real de preço com modelo treinado em regressão  
- Adição de **Dockerfile** e **docker-compose**
