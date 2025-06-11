# app/crud/crud_user.py

from sqlalchemy.orm import Session
from .. import models, schemas # 親ディレクトリの models, schemas パッケージをインポート
from ..core.security import get_password_hash # パスワードハッシュ化関数 (後で作成)

def get_user(db: Session, user_id: int):
    # IDを基にユーザーを1人取得
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    # メールアドレスを基にユーザーを1人取得
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    # ユーザー一覧を取得（ページネーション対応）
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    # 新しいユーザーを作成
    hashed_password = get_password_hash(user.password) # パスワードをハッシュ化
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user) # セッションに新しいユーザーオブジェクトを追加 (まだDBには書き込まれていない)
    db.commit()      # 変更をDBにコミット (保存)
    db.refresh(db_user) # DBから最新の状態（自動採番されたIDなど）をオブジェクトに反映
    return db_user
