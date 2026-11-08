import os, secrets, time

import jwt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

API_KEY = os.getenv('API_KEY', 'ganti-api-key')
JWT_SECRET = os.getenv('JWT_SECRET', 'ganti-jwt-secret')
ADMIN_USER = os.getenv('ADMIN_USER', 'admin')
ADMIN_PASS = os.getenv('ADMIN_PASS', 'ganti-password')

router = APIRouter()

class Login(BaseModel):
    username: str
    password: str

@router.post('/auth/login')
def login(body: Login):
    ok_user = secrets.compare_digest(body.username, ADMIN_USER)
    ok_pass = secrets.compare_digest(body.password, ADMIN_PASS)
    if not (ok_user and ok_pass):
        raise HTTPException(status_code=401, detail='Login gagal')
    token = jwt.encode({'sub': body.username, 'exp': int(time.time()) + 3600},
                       JWT_SECRET, algorithm='HS256')
    return {'access_token': token, 'token_type': 'bearer'}

def require_auth(x_api_key: str = Header(default=''),
                 authorization: str = Header(default='')):
    if x_api_key and secrets.compare_digest(x_api_key, API_KEY):
        return 'service'
    if authorization.startswith('Bearer '):
        try:
            data = jwt.decode(authorization[7:], JWT_SECRET, algorithms=['HS256'])
            return data['sub']
        except jwt.PyJWTError:
            pass
    raise HTTPException(status_code=401, detail='Tidak terautentikasi')
