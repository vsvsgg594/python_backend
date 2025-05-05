# src/routes/token.py
from fastapi.security import HTTPBearer

bearer_scheme = HTTPBearer()

def decode_token(token: str):
    # Your token decoding logic here
    pass