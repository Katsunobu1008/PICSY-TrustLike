# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# --- データベース接続設定 ---
# プロトタイプでは、セットアップ不要なファイルベースのDBであるSQLiteを使用します。
# "sqlite:///./p_t_like.db" は、プロジェクトのルートディレクトリに p_t_like.db というファイルを作成して
# データベースとして使用するという意味です。
SQLALCHEMY_DATABASE_URL = "sqlite:///./p_t_like.db"

# 将来的にPostgreSQLに移行する場合は、以下のように書き換えます。
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/database_name"


# --- SQLAlchemyのコア部分の設定 ---

# 1. データベースエンジン (Engine) の作成
# create_engineは、SQLAlchemyアプリケーションの出発点です。
# connect_args={"check_same_thread": False} はSQLiteを使用する場合にのみ必要なおまじないです。
# FastAPIの非同期な性質とSQLiteがうまく連携するための設定です。
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 2. データベースセッション (Session) を作成するためのクラスを定義
# セッションは、データベースとの個々の対話（トランザクション）を管理します。
# autocommit=False: 自動でコミットしない（明示的に指示するまでDBに保存しない）
# autoflush=False: 自動でDBに中間状態を送信しない
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. データベースモデル（テーブル定義）の基盤となるクラスを作成
# これから作成する全てのデータベースモデルクラスは、このBaseクラスを継承します。
Base = declarative_base()
