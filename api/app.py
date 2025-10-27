from flask import Flask, redirect, url_for
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from flasgger import Swagger
from config import SWAGGER_TEMPLATE
from database import db 

# Importar os Blueprints/models
from routes.auth import auth_bp
from routes.books import books_bp


app = Flask(__name__)
app.config.from_object('config')

# Configuração e Anexação de Extensões
db.init_app(app)
jwt = JWTManager(app)
swagger = Swagger(app, template=SWAGGER_TEMPLATE)
cache = Cache(app)

limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    storage_uri="memory://",
    default_limits=["1000 per day", "100 per hour"]
)

app.register_blueprint(auth_bp) 
app.register_blueprint(books_bp) 

@app.route('/')
def index():
    return redirect(url_for('flasgger.apidocs')) 

if __name__ == '__main__':
    with app.app_context():     
        db.create_all()
    app.run(debug=True)