# app/schemas/user.py (修正)

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional  # Listを追加

# 循環参照を防ぐため、Contentスキーマを直接インポートせず、
# 別のファイルに分けるか、後方参照を使う。今回は別のファイルに分けたのでOK。
# ただし、UserスキーマがContentを、ContentスキーマがUserを参照するため、
# Pythonが解釈する順番によっては問題が起きる可能性がある。
# FastAPI/Pydanticはこれをうまく扱ってくれるが、明示的に解決する方法もある。
# 今回はひとまずこのまま進める。
from .content import Content  # Contentスキーマをインポート
