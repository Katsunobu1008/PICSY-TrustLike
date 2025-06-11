# app/schemas/user.py

from pydantic import BaseModel
from datetime import datetime

# --- APIでやり取りするデータの形式を定義 ---

# ベースとなるスキーマ: 全てのスキーマで共通する属性を定義
class UserBase(BaseModel):
    username: str
    email: str

# ユーザー作成時に受け取るデータ形式
# UserBaseを継承し、password属性を追加
class UserCreate(UserBase):
    password: str

# APIレスポンスとして返すユーザー情報のデータ形式
# UserBaseを継承し、idとcreated_atを追加
# パスワードのような機密情報は含めない
class User(UserBase):
    id: int
    created_at: datetime

    class Config:
        # PydanticモデルがSQLAlchemyモデルなどのORMオブジェクトから
        # データを読み取れるようにするための設定
        orm_mode = True
