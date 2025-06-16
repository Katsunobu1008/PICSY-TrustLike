# app/crud/crud_content.py

from sqlalchemy.orm import Session
from .. import models, schemas


def get_content(db: Session, content_id: int):
    """IDを指定してコンテンツを1件取得する"""
    return db.query(models.Content).filter(models.Content.id == content_id).first()


def get_contents(db: Session, skip: int = 0, limit: int = 100):
    """コンテンツの一覧を取得する"""
    return db.query(models.Content).offset(skip).limit(limit).all()


def create_user_content(db: Session, content: schemas.ContentCreate, user_id: int):
    """指定されたユーザーの新しいコンテンツを作成する"""
    db_content = models.Content(**content.model_dump(), creator_id=user_id)
    db.add(db_content)
    db.commit()
    db.refresh(db_content)
    return db_content
