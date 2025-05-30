import numpy as np
from typing import List, Tuple, Dict
from datetime import datetime

# --- システムのグローバル定数 ---
# これらはPicsyEngineのデフォルト値として使ったり、メイン処理でインスタンスかする際に渡したりする。

DEFALUT_ALPHA_LIKE = 0.5  # 「いいね」一回あたりの標準評価移転量
DEFALUT_ALPHA_LILE_MAX = 0.3  # ユーザーが設定できるalpha?likeの上限
DEFALUT_GAMMA_RATE = 0.1  # 自然回収率
DEFAULT_MAX_ITERATIONS = 1000  # 貢献度計算の最大反復回数
DEFAULT_TOLERANCE = 1e-6  # 貢献度計算の収束判定の許容誤差


class PicsyUser:
    """
    PICSY-TrustLikeシステム内のユーザーを表すクラス
    主にユーザーの識別情報を保持する。
    """

    def __init__(self, user_id: str, username: str):
        """
        PicsyUserオブジェクトを初期化する

        user_id(str):ユーザーの一意なID
        username(str):ユーザーの表示名
        """
        if not user_id:
            raise ValueError("user_idは必須です。")
        if not username:
            raise ValueError("usernameは必須です。")

        self.user_id = user_id
        self.username = username

    def __repr__(self) -> str:
        """
        PicsyUserオブジェクトを分かりやすい文字列で表現します。
        print()関数などでオブジェクトを表示した際に使われます。
        """
        return f"PicsyUser(user_id='{self.user_id}', username='{self.username}')"

    def __eq__(self, other) -> bool:
        """
        2つのPicsyUserオブジェクトが等しいか（user_idが同じか）を比較します。
        リスト内検索などで便利です。
        """
        if isinstance(other, PicsyUser):
            return self.user_id == other.user_id
        return False

    def __hash__(self) -> int:
        """
        オブジェクトを辞書のキーとして使う場合などに必要なハッシュ値を返します。
        user_idに基づいて計算します。
        """
        return hash(self.user_id)
