# routes/books.py

from flask import Blueprint, request, jsonify, url_for, redirect
from flask_jwt_extended import jwt_required
from sqlalchemy import text, func
from math import ceil
from sklearn.ensemble import RandomForestRegressor

# Importações de outros arquivos
from database import db 
from models import User, Book 
from app import cache, limiter # Importamos as instâncias de app.py
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import re
import pandas as pd
from sklearn.preprocessing import  OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
import random


# Baixar os recursos necessários do NLTK (se ainda não tiverem sido baixados)
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab') # Adicionado download de punkt_tab

# Cria o Blueprint
books_bp = Blueprint('books', __name__, url_prefix='/api/v1')

# Rotas de Health e Cache (que afetam a aplicação inteira)


@books_bp.route("health")
def health():
  """
  Verifica se a aplicação está no ar.
  ---
  tags:
    - Books
  responses:
    200:
      description: checa o database com uma consulta simples
  """
  try:    
    db.session.execute(text('SELECT count(1) FROM user;'))
    return jsonify({"status": "ok", "database": "connected"})
  except Exception as e:
      return jsonify({
          "status": "fail",
          "error": str(e)
      }), 500

@books_bp.route('/cache', methods=['POST'])
def clear_cache():
    """
    Limpa todo o cache da aplicação.
    ---
    tags:
      - Cache
    responses:
      200:
        description: Cache limpo com sucesso
    """
    cache.clear()
    return jsonify({"msg": "Cache limpo com sucesso"}), 200

# Rotas de Books e Estatísticas


@books_bp.route('scraping/trigger', methods=['POST'])    
@jwt_required()
def load_books():
  """
    Carrega arquivo de books.csv para o banco de dados.
    ---
    tags:
      - Books
    security:
      - Bearer: []  
    responses:
      201:
        description: Arquivo carregado com sucesso
      400:
        description: Erro ao carregar o arquivo
    """
  try:
    
    db.session.execute(text('TRUNCATE TABLE books;'))
    
    df = pd.read_csv('./scraper/data/books.csv')
    # Remove o símbolo de libra (£) e converte para float
    df['price_numeric'] = df['price'].str.replace('£', '').astype(float)
    # Extrai o número entre parênteses da coluna 'availability'
    extracted_availability = df['availability'].str.extract(r'\((\d+)\s*available\)')
    df['availability_numeric'] = extracted_availability.astype(float).fillna(0).astype(int)

      # Iterate over DataFrame rows and create Book objects
    for index, row in df.iterrows():
        book = Book(
            title=row['title'],
            category=row['category'],
            price=row['price'],
            price_excl_tax=row['price_excl_tax'],
            price_incl_tax=row['price_incl_tax'],
            rating=row['rating'],
            upc=row['upc'],
            availability=row['availability'],
            description=row['description'],
            image_url=row['image_url'],
            book_url=row['book_url'],
            number_of_reviews=row['number_of_reviews'],
            product_type=row['product_type'],
            tax=row['tax'],
            price_numeric=row['price_numeric'],
            availability_numeric=row['availability_numeric']
        )
        db.session.add(book)

    # Commit the session to save data to the database
    db.session.commit()
    return jsonify({"msg": "Books loaded successfully"}), 201 
  except Exception as e:
    return jsonify({"error": str(e)}), 400



@books_bp.route("books", methods=["GET"])
@limiter.limit("5 per 10 minutes", override_defaults=True)
def get_books():
    """
    Busca todos os livros da api com paginação
    ---
    tags:
      - Books
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Número da página.
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: Número de itens por página.
    responses:
      200:
        description: Lista paginada de livros.
        schema:
          type: object
          properties:
            page:
              type: integer
            limit:
              type: integer
            total:
              type: integer
            total_pages:
              type: integer
            data:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  title:
                    type: string
                  category:
                    type: string
                  price:
                    type: string
                  rating:
                    type: string
                  upc:
                    type: string
                  availability:
                    type: string
      """
    # parâmetros de paginação (?page=1&limit=50)
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=50, type=int)

    # usa o paginate do SQLAlchemy
    pagination = db.session.query(Book).paginate(page=page, per_page=limit, error_out=False)

    books = [
        {
            "id": b.id,
            "title": b.title,
            "category": b.category,
            "price": b.price,
            "rating": b.rating,
            "upc": b.upc,
            "availability": b.availability,
        }
        for b in pagination.items
    ]

    return jsonify({
        "page": page,
        "limit": limit,
        "total": pagination.total,
        "total_pages": pagination.pages,
        "data": books
    })


@books_bp.route("books/<int:book_id>", methods=["GET"])
def get_book(book_id):
    """
    Busca livro pelos ID
    ---
    tags:
      - Books
    parameters:
      - name: book_id
        in: path
        type: integer
        required: true
        description: Id do livro que quer buscar.
    responses:
      200:
        description: Informações e detalhes do livro.
      404:
        description: Livro não encontrado.
    """
    book = Book.query.filter_by(id=book_id).first()

    if not book:
        return jsonify({"error": f"Livro com id {id} não encontrado"}), 404

    return jsonify({
        "id": book.id,
        "title": book.title,
        "category": book.category,
        "price": book.price,
        "rating": book.rating,
        "description": book.description,
        "availability": book.availability,
    })
    
@books_bp.route("/stats/overview", methods=["GET"])
def get_stats_overview():
    """
    Estatisticas gerais sobre a base de livros.
    ---
    tags:
      - Statistics
    responses:
      200:
        description: Total de livros, preço médio, média de avaliações.
    """
    total_books = db.session.query(Book).count()
    average_price = db.session.query(func.avg(Book.price_numeric)).scalar()

    # Rating distribution
    rating_distribution = db.session.query(Book.rating, func.count(Book.rating)).group_by(Book.rating).order_by(Book.rating).all()
    rating_distribution_dict = dict(rating_distribution)

    return jsonify({
        "total_books": total_books,
        "average_price": round(average_price, 2) if average_price is not None else 0,
        "rating_distribution": rating_distribution_dict
    })

@books_bp.route("/stats/categories", methods=["GET"])
def get_stats_categories():
    """
    Estatisitcas detalhadas por categoria.
    ---
    tags:
      - Statistics
    responses:
      200:
        description: Estatisticas por categoria de livros, incluindo contagem e preço médio.
    """
    category_stats = db.session.query(
        Book.category,
        func.count(Book.id),
        func.avg(Book.price_numeric)
    ).group_by(Book.category).all()

    category_stats_list = []
    for category, count, avg_price in category_stats:
        category_stats_list.append({
            "category": category,
            "book_count": count,
            "average_price": round(avg_price, 2) if avg_price is not None else 0
        })

    return jsonify(category_stats_list)


@books_bp.route("/top-rated", methods=["GET"])
def get_top_rated_books():
    """
    Lista dos livros melhores avaliados.
    ---
    tags:
      - Books
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Número da página.
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: Número de itens por página.
    responses:
      200:
        description: Lista de livros melhores avaliados.
    """
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=50, type=int)

    pagination = Book.query.order_by(Book.rating.desc()).paginate(page=page, per_page=limit, error_out=False)
    books = pagination.items

    return jsonify({
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
        "data": [{
            "id": book.id,
            "title": book.title,
            "category": book.category,
            "price": book.price,
            "rating": book.rating,
            "availability": book.availability,
        } for book in books]
    })

@books_bp.route("/price-range", methods=["GET"])
def get_books_by_price_range():
    """
    Filtrar livros conforme avaliação eplo .
    ---
    tags:
      - Books
    parameters:
      - name: min
        in: query
        type: number
        required: false
        description: Preço mínimo (opicional).
      - name: max
        in: query
        type: number
        required: false
        description: Preço máximo (opicional).
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Número da página.
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: Número de itens por página.
    responses:
      200:
        description: Lista páginada de livros, de acordo com o preço escolhido.
      400:
        description: Parametros inválidos de preço.
    """
    min_price = request.args.get("min", type=float)
    max_price = request.args.get("max", type=float)
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=50, type=int)


    query = Book.query

    if min_price is not None:
        query = query.filter(Book.price_numeric >= min_price)
    if max_price is not None:
        query = query.filter(Book.price_numeric <= max_price)

    # If no min or max is provided, return all books (or handle as an error if required)
    if min_price is None and max_price is None:
         return jsonify({"error": "Insira os dados de preço mínimo e máximo"}), 400


    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    books = pagination.items

    return jsonify({
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
        "data": [{
            "id": book.id,
            "title": book.title,
            "category": book.category,
            "price": book.price,
            "rating": book.rating,
            "availability": book.availability,
        } for book in books]
    })



@books_bp.route("/search", methods=["GET"])
def search_books():
    """
    Busca livros por título ou categorias paginados.
    ---
    tags:
      - Books
    parameters:
      - name: title
        in: query
        type: string
        required: false
        description: Parte, ou título completo de um livro.
      - name: category
        in: query
        type: string
        required: false
        description: Parte ou categoria comple de um livro.
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Número da página.
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: Número de itens por página.
    responses:
      200:
        description: Lista paginada de livros de acordo com os paramteros de busca.
    """
    title = request.args.get("title")
    category = request.args.get("category")
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=50, type=int)

    query = Book.query

    if title:
        query = query.filter(Book.title.ilike(f"%{title}%"))
    if category:
        query = query.filter(Book.category.ilike(f"%{category}%"))

    pagination = query.paginate(page=page, per_page=limit, error_out=False)
    books = pagination.items


    return jsonify({
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
        "data": [{
            "id": book.id,
            "title": book.title,
            "category": book.category,
            "price": book.price,
            "rating": book.rating,
            "availability": book.availability,
        } for book in books]
    })

@books_bp.route("/categories", methods=["GET"])
def get_categories():
    """
    Todas as categorias únicas de livros.
    ---
    tags:
      - Books
    responses:
      200:
        description: Todas as categorias únicas de livros.
    """
    categories = db.session.query(Book.category).distinct().all()
    return jsonify([cat[0] for cat in categories])

@books_bp.route("ml/features", methods=["GET"])
def get_features():
    """
    Retorna features processadas com paginação.
    ---
    tags:
      - Machine Learning
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: Número da página.
      - name: limit
        in: query
        type: integer
        required: false
        default: 50
        description: Número de itens por página.
    responses:
      200:
        description: Lista paginada de features.
    """

    # parâmetros de paginação (?page=1&limit=50)
    page = request.args.get("page", default=1, type=int)
    limit = request.args.get("limit", default=50, type=int)

    # Faz a query com SQLAlchemy
    query = db.session.query(Book)
    df = pd.read_sql(query.statement, db.engine)

    # === processamento ===
    stop_words = set(stopwords.words())

    def tokenize_and_remove_stopwords(text):
        if isinstance(text, str):
            tokens = word_tokenize(text.lower())
            filtered_tokens = [word for word in tokens if word.isalnum() and word not in stop_words]
            return filtered_tokens
        return []

    df['title_processed'] = df['title'].apply(tokenize_and_remove_stopwords)
    df['description_processed'] = df['description'].apply(tokenize_and_remove_stopwords)

    if pd.api.types.is_string_dtype(df['availability']):
        df['availability'] = df['availability'].apply(lambda x: int(re.search(r'\d+', x).group()))

    df['number_of_reviews'] = df['number_of_reviews'].fillna(0)
    df['price'] = df['price'].astype(str).str.replace('£', '', regex=False).astype(float)
    df['in_stock'] = df['availability'].apply(lambda x: 1 if x > 0 else 0)

    features_to_keep = ['category', 'price', 'rating', 'availability', 'in_stock', 'title_processed', 'description_processed']
    df_processed = df[features_to_keep].copy()

    numerical_features = ['price', 'rating', 'availability', 'in_stock']
    categorical_features = ['category']
    text_features = ['title_processed', 'description_processed']

    preprocessor = ColumnTransformer(
        transformers=[('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)],
        remainder='passthrough'
    )

    processed_data = preprocessor.fit_transform(df_processed)
    onehot_feature_names = preprocessor.named_transformers_['cat'].get_feature_names_out(categorical_features)
    category_names = [name.replace('category_', '').replace(' ', '_') for name in onehot_feature_names]
    all_feature_names = category_names + numerical_features + text_features

    processed_df = pd.DataFrame(processed_data, columns=all_feature_names, index=df.index)

    for col in category_names + ['in_stock']:
        if col in processed_df.columns:
            processed_df[col] = processed_df[col].astype(int)

    # === paginação ===
    total = len(processed_df)
    total_pages = (total + limit - 1) // limit  # arredonda pra cima
    start = (page - 1) * limit
    end = start + limit
    paginated_df = processed_df.iloc[start:end]

    # === retorno ===
    return jsonify({
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "data": paginated_df.to_dict(orient="records")
    })
    

    
@books_bp.route("/ml/training-data", methods=["GET"])
def training_data():
    """
    Retorna uma amostra dos dados preparada para treino/teste de Machine Learning no formato completo.
    ---
    tags:
      - Machine Learning
    parameters:
      - name: sample_size
        in: query
        type: integer
        description: Quantidade de amostras a serem retornadas (padrão 500)
      - name: train_split
        in: query
        type: float
        description: Proporção de treino (padrão 0.8)
      - name: random_state
        in: query
        type: integer
        description: Valor fixo para reprodutibilidade (padrão 42)
    responses:
      200:
        description: Amostra processada para treino e teste.
    """

    # === parâmetros ===
    sample_size = request.args.get("sample_size", default=500, type=int)
    train_split = request.args.get("train_split", default=0.8, type=float)
    random_state = request.args.get("random_state", default=42, type=int)

    # === target padrão ===
    target_col = "price"

    # === query dos dados ===
    query = db.session.query(Book)
    df_total = pd.read_sql(query.statement, db.engine)

    # === pré-processamento ===
    stop_words_portuguese = set(stopwords.words("portuguese"))

    def tokenize_and_remove_stopwords(text):
        if isinstance(text, str):
            tokens = word_tokenize(text.lower())
            return [w for w in tokens if w.isalnum() and w not in stop_words_portuguese]
        return []

    df_total["title_processed"] = df_total["title"].apply(tokenize_and_remove_stopwords)
    df_total["description_processed"] = df_total["description"].apply(tokenize_and_remove_stopwords)
    df_total["price"] = df_total["price"].astype(str).str.replace("£", "", regex=False).astype(float)
    
    if pd.api.types.is_string_dtype(df_total["availability"]):
        df_total["availability"] = df_total["availability"].apply(
            lambda x: int(re.search(r"\d+", x).group()) if re.search(r"\d+", x) else 0
        )

    df_total["in_stock"] = df_total["availability"].apply(lambda x: 1 if x > 0 else 0)
    df_total["number_of_reviews"] = df_total["number_of_reviews"].fillna(0)

    # === One-hot encoding das categorias ===
    all_categories = [
        "Academic","Add_a_comment","Adult_Fiction","Art","Autobiography","Biography",
        "Business","Childrens","Christian","Christian_Fiction","Classics","Contemporary",
        "Crime","Cultural","Default","Erotica","Fantasy","Fiction","Food_and_Drink",
        "Health","Historical","Historical_Fiction","History","Horror","Humor","Music",
        "Mystery","New_Adult","Nonfiction","Novels","Paranormal","Parenting","Philosophy",
        "Poetry","Politics","Psychology","Religion","Romance","Science","Science_Fiction",
        "Self_Help","Sequential_Art","Short_Stories","Spirituality","Sports_and_Games",
        "Suspense","Thriller","Travel","Womens_Fiction","Young_Adult"
    ]

    # Inicializa todas as categorias com 0
    for cat in all_categories:
        df_total[cat] = 0

    # Marca 1 na categoria real do livro (se existir)
    df_total.loc[df_total["category"].notnull(), "category"] = df_total["category"].str.strip()
    for idx, row in df_total.iterrows():
        cat = row["category"]
        if cat in all_categories:
            df_total.at[idx, cat] = 1

    # Seleciona colunas finais
    features_to_keep = all_categories + ["availability", "description_processed",
                                         "in_stock", "price", "rating", "title_processed"]
    df_total = df_total[features_to_keep]

    # === amostra reprodutível ===
    df = df_total.sample(n=min(sample_size, len(df_total)), random_state=random_state)

    # === split treino/teste ===
    X = df.drop(columns=[target_col])
    y = df[target_col]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, train_size=train_split, random_state=random_state
    )

    # === resultado final ===
    result = {
        "data": pd.concat([X_train, y_train], axis=1).to_dict(orient="records"),
        "limit": sample_size,
        "page": 1,
        "total": len(df_total),
        "total_pages": ceil(len(df_total) / sample_size)
    }

    return jsonify(result)
  
default_book = {
  "category": "Travel",
  "rating": 3,
  "availability": 5,
  "in_stock": 1,
  "number_of_reviews": 0,
  "title_processed": ["example"],
  "description_processed": ["example", "description"]
}


@books_bp.route("/ml/predictions", methods=["POST"])
def predict_price():
    """
    Recebe dados de um livro e retorna previsão de preço (simulada).
    ---
    tags:
      - Machine Learning
    parameters:
      - in: body         # Sintaxe que funciona para você
        name: body
        required: true
        schema:
          type: object
          # Adicione o 'example' aqui para preencher o corpo de exemplo
          example:
            category: "Travel"
            rating: 3
            availability: 5
            in_stock: 1
            number_of_reviews: 0
            title_processed: ["science", "fiction"]
            description_processed: ["a", "thrilling", "novel"]
          properties:
            category:
              type: string
              default: "Travel"
            rating:
              type: integer
              default: 3
            availability:
              type: integer
              default: 5
            in_stock:
              type: integer
              default: 1
            number_of_reviews:
              type: integer
              default: 0
            title_processed:
              type: array
              items:
                type: string
              default: ["example"]
            description_processed:
              type: array
              items:
                type: string
              default: ["example", "description"]
    responses:
      200:
        description: Predição do preço do livro
    """

    data = request.get_json(force=True, silent=True) or {}
    book_data = {k: data.get(k, v) for k, v in default_book.items()}
    
    predicted_price = round(random.uniform(10, 50), 2)

    return jsonify({
        "predicted_price": predicted_price,
        "input": book_data
    })