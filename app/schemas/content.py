# app/schemas/content.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .user import User  # 循環参照を避けるため、Userスキーマをインポート

# ベーススキーマ


class ContentBase(BaseModel):
    title: str
    body: Optional[str] = None  # 本文は省略可能とする

# コンテンツ作成時に受け取るデータ形式


class ContentCreate(ContentBase):
    pass

# APIレスポンスとして返すコンテンツ情報のデータ形式


class Content(ContentBase):
    id: int
    creator_id: int
    created_at: datetime
    creator: User  # 作成者のユーザー情報もネストして含める

    class Config:
        from_attributes = True
