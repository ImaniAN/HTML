from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime

class Auth:
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def hash_password(self, password):
        return generate_password_hash(password)

    def verify_password(self, hashed_password, password):
        return check_password_hash(hashed_password, password)

    def generate_token(self, user_id):
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                self.secret_key,
                algorithm='HS256'
            )
        except Exception as e:
            return None

    def verify_token(self, token):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Token expired'
        except jwt.InvalidTokenError:
            return 'Invalid token'
