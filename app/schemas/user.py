# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List

# Pydanticの循環参照問題を解決するために、Contentを直接インポートせず、
# forward reference を使うか、モデルのリビルドを行う。
# FastAPIでは多くの場合自動で解決されるため、まずはこの形で実装する。
from .content import Content

# ベーススキーマ


class UserBase(BaseModel):
    username: str
    email: EmailStr

# ユーザー作成時に受け取るデータ形式


class UserCreate(UserBase):
    password: str

# APIレスポンスとして返すユーザー情報のデータ形式


class User(UserBase):
    id: int
    created_at: datetime
    contents: List[Content] = []

    class Config:
        from_attributes = True

# Pydanticの循環参照問題を解決するおまじない
# FastAPI v0.95以降では自動化が進んでいるが、明示的に行うとより確実
# User.model_rebuild() # Python 3.11以降ではUpdateForwardRefsが推奨されるが、FastAPIが内部で処理
