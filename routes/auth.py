# routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from sqlalchemy import text 
from werkzeug.security import generate_password_hash, check_password_hash
from database import db 
from models import User 
from extensions import limiter

# Cria o Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per 10 minutes", override_defaults=True)
def register_user():
    """
    Registra um novo usuário.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      201:
        description: Usuário criado com sucesso
      400:
        description: Usuário já existe
    """
    data = request.get_json()
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"error": "User already exists"}), 400
    
    # Criptografa a senha com um algoritmo seguro (PBKDF2)
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256', salt_length=16)

    new_user = User(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"msg": "User created"}), 201


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per 10 minutes", override_defaults=True)
def login():
    """
    Faz login do usuário e retorna um JWT.
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login bem sucedido, retorna JWT
      401:
        description: Credenciais inválidas
    """
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and check_password_hash(user.password, data['password']):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return jsonify(access_token=access_token, refresh_token=refresh_token), 200

    
    return jsonify({"error": "Credenciais inválidas"}), 401


@auth_bp.route('/protected', methods=['GET'])
@limiter.limit("1 per 1 minutes", override_defaults=True)
@jwt_required()
def protected():
    """
    Rota criada para teste de autenticação JWT e ataques de sobrecarga.
    Permitido uma chamada a cada minuto.
    Retorno o ID do usuário autenticado somente se estiver autenticado.
    ---
    tags:
      - Authentication
    security:
      - Bearer: []
    responses:
      201:
        description: success
      401:
        description: Token não fornecido ou inválido
    """
    current_user_id = get_jwt_identity()  # Retorna o 'identity' usado na criação do token
    return jsonify({"msg": f"Usuário com ID {current_user_id} acessou a rota protegida."}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # Require a valid refresh token to access this route
def refresh():
    """
    Renova o token de acesso usando um refresh token válido.
    ---
    tags:
      - Authentication
    parameters:
      - in: header
        name: Authorization
        description: Refresh token (Bearer token)
        required: true
        type: string
    responses:
      200:
        description: Novo token de acesso gerado com sucesso
      401:
        description: Refresh token inválido ou expirado
    """
    current_user = get_jwt_identity() # Get the identity from the refresh token
    new_access_token = create_access_token(identity=current_user) # Create a new access token
    return jsonify(access_token=new_access_token), 200  