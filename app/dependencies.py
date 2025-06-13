# app/dependencies.py

from .database import SessionLocal  # database.pyで定義したSessionLocalをインポート


def get_db():
    """
    APIエンドポイントにデータベースセッションを提供する依存関係関数。
    処理の開始時にセッションを開始し、終了時に（成功・失敗にかかわらず）必ずセッションを閉じる。
    """
    db = SessionLocal()  # セッションのインスタンスを作成
    try:
        # yieldキーワードは、このセッションオブジェクト(db)をAPIエンドポイント内の処理に「提供」する
        yield db
    finally:
        # APIエンドポイントの処理が終わった後、必ずこのブロックが実行される
        db.close()  # セッションを閉じることで、データベース接続を解放する
