# ファイル先頭のfrom sqlalchemy import ... に追加
from sqlalchemy.orm import relationship


class User(Base):
    # ... 既存のid, usernameなどの定義 ...

    # Contentモデルとのリレーションシップを定義
    # "contents"という名前で、このUserオブジェクトから、その人が作成したContentオブジェクトのリストにアクセスできる
    contents = relationship("Content", back_populates="creator")
