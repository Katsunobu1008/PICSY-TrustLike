# picsy_engine_prototype.py

import numpy as np
from typing import List, Tuple, Dict
from datetime import datetime

# --- システムのグローバル定数 ---
DEFAULT_ALPHA_LIKE = 0.05
DEFAULT_ALPHA_LIKE_MAX = 0.3
DEFAULT_GAMMA_RATE = 0.1
DEFAULT_MAX_ITERATIONS = 1000
DEFAULT_TOLERANCE = 1e-6


class PicsyUser:
    """
    PICSY-TrustLikeシステム内のユーザーを表すクラス
    主にユーザーの識別情報を保持する。
    """

    def __init__(self, user_id: str, username: str):
        if not user_id:
            raise ValueError("user_idは必須です。")
        if not username:
            raise ValueError("usernameは必須です。")
        self.user_id = user_id
        self.username = username

    def __repr__(self) -> str:
        return f"PicsyUser(user_id='{self.user_id}', username='{self.username}')"

    def __eq__(self, other) -> bool:
        if isinstance(other, PicsyUser):
            return self.user_id == other.user_id
        return False

    def __hash__(self) -> int:
        return hash(self.user_id)


class PicsyEngine:
    """
    PICSY-TrustLikeシステムのコアロジックを管理・実行するエンジンクラス。
    評価行列Eの保持、貢献度cの計算、取引（いいね）、自然回収などを行う。
    """

    def __init__(self,
                 user_list: List[PicsyUser],
                 alpha_like_default: float = DEFAULT_ALPHA_LIKE,
                 alpha_like_max: float = DEFAULT_ALPHA_LIKE_MAX,
                 gamma_rate: float = DEFAULT_GAMMA_RATE,
                 max_iterations: int = DEFAULT_MAX_ITERATIONS,
                 tolerance: float = DEFAULT_TOLERANCE):
        """
        PicsyEngineを初期化します。

        Args:
            user_list (List[PicsyUser]): システムに参加するユーザーオブジェクトのリスト。
            alpha_like_default (float): 「いいね」1回あたりのデフォルト評価移転量。
            alpha_like_max (float): ユーザーが設定できるalpha_likeの最大値。
            gamma_rate (float): 自然回収率。
            max_iterations (int): 貢献度計算時の最大反復回数。
            tolerance (float): 貢献度計算時の収束許容誤差。
        """
        if not user_list:
            raise ValueError("ユーザーリストが空です。最低1人以上のユーザーが必要です。")
        if len(user_list) <= 1 and len(user_list) > 0:  # 1人の場合、N-1がゼロ除算になる
            print(
                f"警告: ユーザー数が1人のため、貢献度計算は機能しませんが初期化は行います。({user_list[0].username})")
            # raise ValueError("ユーザー数が1以下です。貢献度計算のためには2人以上必要です。")
            # N=1の場合のE'の定義はPICSYの原典にも無いため、ここでは許容し、計算時にエラーを出すか、
            # 特殊な処理（例：貢献度=1）をする。今回は後述の計算メソッドでnum_users <=1 のチェックを入れる。

        self.users: List[PicsyUser] = user_list
        self.num_users: int = len(self.users)

        # ユーザーIDと行列インデックスのマッピングを作成 (効率的なアクセスと拡張性のため)
        self.user_id_to_index: Dict[str, int] = {
            user.user_id: i for i, user in enumerate(self.users)
        }
        # インデックスからユーザー名を取得するための逆引き辞書 (表示用)
        self.user_index_to_name: Dict[int, str] = {
            i: user.username for i, user in enumerate(self.users)
        }
        # インデックスからユーザーIDを取得するための逆引き辞書 (ログ用など)
        self.user_index_to_id: Dict[int, str] = {
            i: user.user_id for i, user in enumerate(self.users)
        }

        # システムパラメータの設定
        if not (0 < alpha_like_default <= alpha_like_max):
            raise ValueError(
                "alpha_like_defaultは0より大きく、alpha_like_max以下である必要があります。")
        if not (0 < alpha_like_max < 1.0):  # 1いいねで予算が全て無くなるのは極端
            raise ValueError("alpha_like_maxは0より大きく1.0未満である必要があります。")
        if not (0 <= gamma_rate < 1.0):
            raise ValueError("gamma_rateは0以上1.0未満である必要があります。")

        self.alpha_like_default: float = alpha_like_default
        self.alpha_like_max: float = alpha_like_max
        self.gamma_rate: float = gamma_rate
        self.max_iterations: int = max_iterations
        self.tolerance: float = tolerance

        # ユーザーごとの「1いいね」評価量設定 (初期値はシステムデフォルト)
        self.user_alpha_settings: Dict[str, float] = {
            user.user_id: self.alpha_like_default for user in self.users
        }

        # 評価行列 E (N x N)
        # 初期状態: 各ユーザーの予算(E_ii)が1.0、他者評価(E_ij, j!=i)が0.0
        self.E: np.ndarray = np.zeros(
            (self.num_users, self.num_users), dtype=float)
        if self.num_users > 0:  # ユーザーが1人以上いる場合のみ実行
            np.fill_diagonal(self.E, 1.0)  # 対角成分（予算E_ii）を1.0に設定

        # 「いいね」のログ (誰が、誰のコンテンツに、いつ、どのくらいの評価量でいいねしたか)
        # Tuple: (liker_id, liked_creator_id, alpha_used, timestamp)
        self.like_log: List[Tuple[str, str, float, datetime]] = []

        # システムの状態変数
        self.current_day: int = 0
        self.current_phase: str = "朝"  # 例: "朝", "昼", "晩"
        self.contribution_calculation_count: int = 0  # 貢献度を計算した回数

        # 貢献度計算用行列E'と貢献度ベクトルc（初期値はNone。最初の貢献度計算で設定される）
        self.E_prime: np.ndarray = None
        self.c_vector: np.ndarray = None

        print(f"\nPICSYエンジンを{self.num_users}人のユーザーで起動しました。")
        user_name_list_str = ", ".join([user.username for user in self.users])
        print(f"  参加ユーザー: {user_name_list_str}")
        print(
            f"  デフォルトα_like: {self.alpha_like_default}, 最大α_like: {self.alpha_like_max}, γ: {self.gamma_rate}")
        print(
            f"  貢献度計算設定 - 最大反復: {self.max_iterations}, 許容誤差: {self.tolerance}")

        # エンジン初期化時に、最初の評価行列と貢献度を表示
        if self.num_users > 0:
            self.display_E(title="初期評価行列 E^(0)")
            self.calculate_all_contributions()  # 初期貢献度を計算 & 表示
