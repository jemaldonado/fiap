# Importa o db de nosso novo arquivo
from database import db 
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

# --- Modelos de Banco de Dados ---

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

    def set_password(self, password):
        self.password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=16)

    def check_password(self, password):
        return check_password_hash(self.password, password)
   
class Book(db.Model):
    __tablename__ = 'books'
    # ... (restante da definição do Book, omitida por brevidade)
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    category = db.Column(db.String)
    price = db.Column(db.String)
    price_excl_tax = db.Column(db.Float)
    price_incl_tax = db.Column(db.Float)
    rating = db.Column(db.Integer)
    upc = db.Column(db.String)
    availability = db.Column(db.String)
    description = db.Column(db.String)
    image_url = db.Column(db.String)
    book_url = db.Column(db.String)
    number_of_reviews = db.Column(db.Integer)
    product_type = db.Column(db.String)
    tax = db.Column(db.Float)
    price_numeric = db.Column(db.Float)
    availability_numeric = db.Column(db.Integer)
    
    def to_dict(self):
        # ... (método de serialização)
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "price": self.price,
            "rating": self.rating,
            "upc": self.upc,
            "availability": self.availability,
        }