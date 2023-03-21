import base64
from functools import wraps
from flask import request
from flask_restful import abort
from decouple import config

def check_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        authorization = request.headers.get('Authorization')
        try:
            decoded = base64.b64decode(authorization)
            print(decoded.decode('utf-8'))
            if decoded.decode('utf-8') == config('AUTH_TOKEN'):
                return func(*args, **kwargs)
            abort(401)
        except Exception as e:
            print(e)
            abort(401)
    return wrapper