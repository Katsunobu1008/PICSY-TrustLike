# app/core/security.py

from passlib.context import CryptContext

# パスワードのハッシュ化方式を指定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化済みパスワードを比較"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """平文パスワードをハッシュ化"""
    return pwd_context.hash(password)
