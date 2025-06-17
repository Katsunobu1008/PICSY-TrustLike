# app/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
# ... (他のインポート) ...
from jose import JWTError, jwt
from ..schemas import TokenData  # TokenDataスキーマをインポート

# ... (router定義はそのまま) ...

# "/auth/token"というパスからトークンを取得するOAuth2スキームを定義
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


async def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    リクエストヘッダーのJWTトークンを検証し、対応するユーザーを返す依存関係。
    認証が必要なエンドポイントでこの関数をDependsに指定して使用する。
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # トークンをデコードしてペイロード（中身）を取得
        payload = jwt.decode(token, security.SECRET_KEY,
                             algorithms=[security.ALGORITHM])
        # ペイロードからユーザーのメールアドレスを取得
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        # TokenDataスキーマでペイロードの形式を検証
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    # メールアドレスを使ってDBからユーザー情報を取得
    user = crud.crud_user.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
    return user  # 認証されたユーザーオブジェクトを返す

# ... (login_for_access_token 関数はそのまま) ...
