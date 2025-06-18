# app/schemas/content.py

from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Pydanticモデルは、循環参照を防ぐために、型ヒント内では
# 別のモデルを文字列として参照できる。しかし、それではエディタの補完が効かないため、
# 通常は直接インポートし、Pydanticの機能で解決する。
# ここでは、Userスキーマの定義が複雑になるのを避けるため、簡易的なスキーマをネストする。


class ContentCreator(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True


class ContentBase(BaseModel):
    title: str
    body: Optional[str] = None


class ContentCreate(ContentBase):
    pass


class Content(ContentBase):
    id: int
    creator_id: int
    created_at: datetime
    creator: ContentCreator  # 作成者のユーザー情報は、パスワードなどを含まない簡易版にする

    class Config:
        from_attributes = True
