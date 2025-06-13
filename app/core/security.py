# app/core/security.py

from datetime import datetime, timedelta, timezone  # timezoneを追加
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import SECRET_KEY, ALGORITHM  # この行が正しく動作するようになります

# パスワードのハッシュ化方式としてbcryptを指定
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """平文パスワードとハッシュ化済みパスワードを比較して真偽を返す"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """平文パスワードを受け取り、ハッシュ化して返す"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """JWTアクセストークンを作成する"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # 有効期限が指定されなかった場合は15分に設定
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
