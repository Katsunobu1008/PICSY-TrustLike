# app/schemas/token.py

from pydantic import BaseModel


class Token(BaseModel):
    """
    APIがクライアントに返すアクセストークンの形式を定義するスキーマ。
    """
    access_token: str
    token_type: str


class TokenData(BaseModel):
    """
    JWTトークンのペイロード（中身）に含まれるデータの形式を定義するスキーマ。
    """
    email: str | None = None
