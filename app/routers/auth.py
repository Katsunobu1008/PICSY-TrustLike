# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from .. import crud, schemas
from ..dependencies import get_db
from ..core import security
from ..core.config import ACCESS_TOKEN_EXPIRE_MINUTES  # トークンの有効期限をconfigから取得

router = APIRouter(
    prefix="/auth",  # 認証関連のエンドポイントは "/auth" で始まる
    tags=["Authentication"]
)


@router.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    """
    ユーザー名（このシステムではメールアドレス）とパスワードでログインし、
    アクセストークンを発行する。
    """
    # ユーザーをメールアドレスで認証
    user = crud.crud_user.get_user_by_email(
        db, email=form_data.username)  # form_data.usernameにメールアドレスが入る

    # ユーザーが存在しない、またはパスワードが一致しない場合はエラー
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # アクセストークンの有効期限を設定
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # アクセストークンを作成 (ペイロードにユーザーID(subject)を含める)
    access_token = security.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # トークンを返す
    return {"access_token": access_token, "token_type": "bearer"}
