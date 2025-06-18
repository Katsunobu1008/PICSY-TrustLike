# app/core/config.py

# --- JWT認証関連の設定 ---
# このSECRET_KEYは、JWTトークンの署名に使われる非常に重要な秘密鍵です。
# 外部に漏洩しないように厳重に管理する必要があります。
# 実際のアプリケーションでは、もっとランダムで複雑な文字列を使用してください。
# 例: Pythonの対話モードで `import secrets; secrets.token_hex(32)` を実行して生成するなど。
# 必ずご自身の秘密の文字列に変更してください
SECRET_KEY: str = "d8e2a3f5b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4"

# JWTの署名に使用するアルゴリズム
ALGORITHM: str = "HS256"

# アクセストークンの有効期限（分単位）
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30


# --- PICSY Engineのデフォルトパラメータ ---
# これらの値は、PicsyEngineクラスの初期化時にデフォルト値として使用されます。
DEFAULT_ALPHA_LIKE: float = 0.05
DEFAULT_ALPHA_LIKE_MAX: float = 0.3
DEFAULT_GAMMA_RATE: float = 0.1
DEFAULT_MAX_ITERATIONS: int = 100
DEFAULT_TOLERANCE: float = 1e-7


# --- データベース接続設定 ---
# プロトタイプでは、セットアップ不要なファイルベースのDBであるSQLiteを使用します。
# "sqlite:///./p_t_like.db" は、プロジェクトのルートディレクトリに p_t_like.db というファイルを作成して
# データベースとして使用するという意味です。
DATABASE_URL: str = "sqlite:///./p_t_like.db"

# 将来的にPostgreSQLに移行する場合は、以下のように書き換えます。
# DATABASE_URL = "postgresql://user:password@host:port/database_name"
