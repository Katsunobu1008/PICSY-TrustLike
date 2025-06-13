# app/routers/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import crud, models, schemas  # crud, models, schemasパッケージをインポート
from ..dependencies import get_db  # get_db依存関係をインポート

# APIRouterインスタンスを作成。これにより、APIエンドポイントをグループ化できる。
router = APIRouter(
    prefix="/users",  # このルーターのエンドポイントは全て "/users" で始まる
    tags=["Users"],    # APIドキュメントでのグループ名
)


@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    新しいユーザーを登録するエンドポイント。
    - **email**: 登録するユーザーのメールアドレス
    - **password**: パスワード
    - **username**: ユーザー名
    """
    # 既に同じメールアドレスのユーザーが存在しないか確認
    db_user = crud.crud_user.get_user_by_email(db, email=user.email)
    if db_user:
        # 既に存在する場合は、400 Bad Requestエラーを返す
        raise HTTPException(status_code=400, detail="Email already registered")

    # 存在しない場合は、新しいユーザーを作成
    created_user = crud.crud_user.create_user(db=db, user=user)
    return created_user
