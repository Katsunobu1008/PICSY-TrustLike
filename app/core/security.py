# app/core/security.py

from passlib.context import CryptContext
# app/core/security.py (追記)
from datetime import datetime, timedelta, timezone  # timezoneを追加
from typing import Optional
from jose import JWTError, jwt
from .config import SECRET_KEY, ALGORITHM  # configから秘密鍵とアルゴリズムをインポート


# パスワードのハッシュ化方式を指定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化済みパスワードを比較"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """平文パスワードをハッシュ化"""
    return pwd_context.hash(password)
# ... verify_password, get_password_hash は既に実装済み ...


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
