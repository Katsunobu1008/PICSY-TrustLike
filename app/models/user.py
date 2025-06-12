# app/models/user.py

from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func # デフォルトの日時を生成するため

from ..database import Base # ステップ1.2.2で作成したBaseクラスをインポート

class User(Base):
    __tablename__ = "users" # このモデルが対応するデータベースのテーブル名

    # --- カラム（テーブルの列）の定義 ---
    id = Column(Integer, primary_key=True, index=True)
    # primary_key=True: このカラムがテーブルの主キー（各行を一意に識別するID）であることを示す
    # index=True: このカラムでデータを検索することが多いため、検索を高速化するためのインデックスを作成する

    username = Column(String, unique=True, index=True, nullable=False)
    # unique=True: 同じusernameを持つユーザーは複数存在できない
    # nullable=False: このカラムは空（NULL）であってはならない

    email = Column(String, unique=True, index=True, nullable=False)

    hashed_password = Column(String, nullable=False) # パスワードはハッシュ化して保存

    # server_default=func.now() は、レコード作成時にデータベース側で現在時刻を自動的に設定する
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    # onupdate=func.now() は、レコード更新時に現在時刻を自動的に設定する
