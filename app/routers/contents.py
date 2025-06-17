# app/routers/contents.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas
from ..dependencies import get_db
from .auth import get_current_user  # 認証済みユーザーを取得する依存関係をインポート

router = APIRouter(
    prefix="/contents",
    tags=["Contents"]
)


@router.post("/", response_model=schemas.Content)
def create_content(
    content: schemas.ContentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)  # 認証を要求
):
    """
    認証済みユーザーとして新しいコンテンツを投稿する。
    """
    return crud.crud_content.create_user_content(db=db, content=content, user_id=current_user.id)


@router.get("/", response_model=List[schemas.Content])
def read_contents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    コンテンツの一覧を取得する。
    """
    contents = crud.crud_content.get_contents(db, skip=skip, limit=limit)
    return contents


@router.get("/{content_id}", response_model=schemas.Content)
def read_content(content_id: int, db: Session = Depends(get_db)):
    """
    IDを指定して単一のコンテンツを取得する。
    """
    db_content = crud.crud_content.get_content(db, content_id=content_id)
    if db_content is None:
        raise HTTPException(status_code=404, detail="Content not found")
    return db_content
