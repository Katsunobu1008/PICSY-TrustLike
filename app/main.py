# app/main.py

# FastAPIライブラリからFastAPIクラスをインポート
from .routers import auth, users  # 作成したルーターをインポート
from fastapi import FastAPI

# --- データベース関連のインポート ---
# これらは、アプリケーション起動時にデータベーステーブルを自動作成するために必要です。
# appディレクトリ内のdatabase.pyから、データベースエンジン(engine)と、
# モデルの基底クラス(Base)をインポートします。
from .database import engine, Base
# appディレクトリ内のmodelsパッケージをインポートします。
# これにより、modelsディレクトリ内の全モデルクラス(user.pyなど)がBaseに認識されます。
from . import models

# --- アプリケーション起動時のデータベーステーブル作成 ---
# Base.metadata.create_all()は、Baseを継承している全てのモデルクラス(現時点ではUserクラス)を
# データベース内で検出し、対応するテーブルがまだ存在しない場合にのみ作成します。
# 開発初期段階では非常に便利な機能ですが、本番環境ではAlembicのような
# マイグレーションツールを使ってデータベーススキーマを管理するのが一般的です。
models.Base.metadata.create_all(bind=engine)


# --- FastAPIアプリケーションのインスタンス作成 ---
# ここで作成された`app`オブジェクトが、API全体の中心となります。
# titleやdescriptionは、自動生成されるAPIドキュメントに表示されます。
app = FastAPI(
    title="PICSY-TrustLike API",
    description="PICSYモデルを応用した「いいね」ベースの評価貨幣システムAPI",
    version="0.1.0"
)
# --- APIルーターのインクルード ---

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])

# --- APIルーターのインクルード（将来のステップで追加） ---
# 今後、機能ごと（認証、ユーザー、コンテンツなど）にファイルを分けてAPIを実装していきます。
# それらのファイルを「ルーター」として、ここで一元的にアプリケーションに登録します。
# 現時点ではコメントアウトしておき、各APIを実装する際にコメントを外していきます。
#
# from .routers import auth, users, contents, likes, picsy_dashboard
#
# app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(users.router, prefix="/users", tags=["Users"])
# app.include_router(contents.router, prefix="/contents", tags=["Contents"])
# app.include_router(likes.router, prefix="/likes", tags=["Likes"])
# app.include_router(picsy_dashboard.router, prefix="/dashboard", tags=["PICSY Dashboard"])


# --- PICSYコアエンジンインスタンスの準備（将来のステップで追加） ---
# この場所に、アプリケーション全体で共有するPICSYエンジンのインスタンスを作成するコードを記述します。
# サーバー起動時にデータベースからユーザー情報を読み込んでエンジンを初期化する、といった処理になります。
# フェーズ1の後半で、実際にエンジンをAPIから利用する際に実装します。
#
# from .core.picsy_engine import PicsyEngine, PicsyUser
# from .crud import crud_user
# from .database import SessionLocal
#
# db = SessionLocal()
# initial_users_from_db = crud_user.get_users(db)
# db.close()
#
# # PicsyUserオブジェクトのリストに変換
# initial_picsy_users = [PicsyUser(user_id=u.id, username=u.username) for u in initial_users_from_db]
#
# # グローバルなPICSYエンジンインスタンス
# picsy_engine_instance = PicsyEngine(user_list=initial_picsy_users)


# --- ルートエンドポイントの定義 ---
# エンドポイントとは、APIが外部からのリクエストを受け付ける具体的なURLのことです。
@app.get("/")
async def read_root():
    """
    APIのルートURL ("/") にGETリクエストが来た時に実行される関数。
    簡単な挨拶メッセージをJSON形式で返します。
    サーバーが正常に起動しているかを確認するための、最も基本的なエンドポイントです。
    """
    return {"message": "PICSY-TrustLike API へようこそ！"}
