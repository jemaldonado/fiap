from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

jwt = JWTManager()
cache = Cache()
limiter = Limiter(key_func=get_remote_address)
