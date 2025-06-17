# app/main.py (中盤部分)

# ... (Base.metadata.create_all(...) の後) ...

from .routers import auth, users, contents  # contentsを追加
app = FastAPI(...)

# --- APIルーターのインクルード ---

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(contents.router, prefix="/contents",
                   tags=["Contents"])  # この行を追加

# ... (ルートエンドポイントの定義はそのまま) ...
