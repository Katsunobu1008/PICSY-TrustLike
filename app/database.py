# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .core.config import DATABASE_URL

# SQLAlchemyのデータベースエンジンを作成
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# データベースセッションを作成するためのクラス
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# データベースモデルの基底クラス
Base = declarative_base()
