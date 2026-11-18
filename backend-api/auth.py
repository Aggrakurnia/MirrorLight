from fastapi import APIRouter

router = APIRouter()

def require_auth():
    return 'dev'