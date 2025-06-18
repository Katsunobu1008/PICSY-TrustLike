# app/dependencies.py

from .database import SessionLocal


def get_db():
    """
    APIエンドポイントにデータベースセッションを提供する依存関係関数。
    処理の開始時にセッションを開始し、終了時に（成功・失敗にかかわらず）必ずセッションを閉じる。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
