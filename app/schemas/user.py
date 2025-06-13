# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from datetime import datetime

# --- APIでやり取りするデータの形式を定義 ---

# ベースとなるスキーマ: 全てのスキーマで共通する属性を定義


class UserBase(BaseModel):
    username: str
    email: EmailStr  # メールアドレス形式を自動で検証

# ユーザー作成時にAPIが受け取るデータ形式
# UserBaseを継承し、password属性を追加


class UserCreate(UserBase):
    password: str

# 【ここが重要】データベースから読み取ったユーザー情報を表すスキーマ
# このクラスが不足していたことがエラーの原因です。


class UserInDBBase(UserBase):
    id: int
    created_at: datetime

    class Config:
        # Pydantic V2以降では 'orm_mode' は 'from_attributes' に変更されました。
        # この設定により、PydanticモデルがSQLAlchemyモデルのようなORMオブジェクトから
        # データを読み取れるようになります。
        from_attributes = True  # orm_mode から変更

# APIがレスポンスとして返すユーザー情報のデータ形式
# UserInDBBaseを継承しているため、id, username, email, created_at を持ちます。
# パスワードのような機密情報は含みません。


class User(UserInDBBase):
    pass  # UserInDBBaseの属性をそのまま使います
