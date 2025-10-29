from flask import Flask, redirect, url_for
from flasgger import Swagger
from config import Config
from database import db
from extensions import jwt, cache, limiter
import warnings
warnings.filterwarnings("ignore", message="Using the in-memory storage")


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializa extensões
    db.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    Swagger(app, template=Config.SWAGGER_TEMPLATE)

    # Importa e registra os blueprints
    from routes.auth import auth_bp
    from routes.books import books_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(books_bp)

    @app.route('/')
    def index():
        return redirect(url_for('flasgger.apidocs'))

    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
