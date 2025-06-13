# app/models/__init__.py

# user.py で定義された User クラスを、
# models パッケージの属性として外部からアクセスできるようにします。
# これにより、他のファイルから from .. import models として、models.User のように参照できます。
from .user import User

# 将来的に Content や Like モデルを追加した場合、ここにも追記します。
# from .content import Content
# from .like import Like
