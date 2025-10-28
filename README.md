# 📚 Books API — Flask Web Scraper e API com Machine Learning

Este projeto consiste em uma aplicação **Python Flask** que realiza **web scraping** do site [Books to Scrape](https://books.toscrape.com/), salva os dados localmente em `.csv`, armazena-os em um banco **PostgreSQL** e disponibiliza uma **API RESTful documentada com Swagger** para consultas, estatísticas e endpoints de machine learning.

---

## 🧩 Estrutura do Projeto

```
api/
├── app.py                # Inicialização principal da aplicação Flask
├── config.py             # Configurações da aplicação e do Swagger
├── database.py           # Configuração da conexão com o banco PostgreSQL
├── models.py             # Definição das classes User e Book
├── routes/
│   ├── auth.py           # Rotas de autenticação e JWT
│   └── books.py          # Rotas de livros, estatísticas e ML
├── scraper/
│   ├── books_scraper.py  # Script de scraping que coleta os dados do site
│   └── data/
│       └── books.csv     # Arquivo CSV gerado com os dados coletados
└── requirements.txt       # Dependências do projeto
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

No arquivo `config.py`, defina a string de conexão PostgreSQL:

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

---

## 📊 Estatísticas

| Método | Endpoint | Descrição |
|:-------|:----------|:-----------|
| GET | /api/v1/stats/overview | Total de livros, preço médio, distribuição de ratings |
| GET | /api/v1/stats/categories | Estatísticas detalhadas por categoria |

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

- **Python 3.10+**
- **Flask** (Framework principal)
- **Flasgger** (Documentação Swagger)
- **Flask-JWT-Extended** (Autenticação com JWT)
- **Flask-Limiter** (Rate limiting)
- **Flask-Caching** (Cache)
- **SQLAlchemy** (ORM e persistência no PostgreSQL)
- **Pandas**, **Scikit-Learn**, **NLTK** (Processamento e ML)
- **Requests**, **BeautifulSoup** (Scraping)

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
