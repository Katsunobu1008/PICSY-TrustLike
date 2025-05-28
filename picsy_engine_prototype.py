import numpy as np
from typing import List, Tuple, Dict

# ---システムの基本設計---

ALPHA_LIKE = 0.05  # 「いいね」一回あたりの標準評価移転料
GAMMA_RATE = 0.01  # 自然回収率


class PicsyUser:
    def __init__(self, user_id: str, username: str, num_total_users: int):
        self.user_id: str = user_id
        self.username: str = username
        self.num_total_user: int = num_total_users

        # 評価行 E_i*(ユーザーiの評価)
        # 初期状態: 自己評価（予算）E_iiが1.0,他者評価(E_ij,j!=i)は0.0
        self.evaluations: np.ndarray = np.zeros(num_total_users, dtype=float)
        # PicsyEngineが初期化時に全ユーザーの予算を1に設定する方針にするが、一旦すべての行は0にする

    def get_budget(self, user_index: int) -> float:
        return self.evaluations[user_index]

    def get_evaluation_to(self, target_user_index: int) -> float:
        return self.evaluations[target_user_index]

    def __repr__(self) -> str:
        return f"PicsyUser(user_id={self.user_id}, username={self.username}, evals ={self.evaluations})"


class PicsyEngine:
    def __init__(self, user_ids: List[str], user_names: List[str], alpha_like: float, gamma_rate: float):
        self.num_users: int = len(user_ids)
        if self.num_users <= 1:
            raise ValueError("ユーザー数が1以下です。ユーザー数は2以上である必要があります。")
    # ユーザー情報を保持するためのリストを作成
    self.user_ids: List[str] = user_ids
    self.user_names: List[str] = user_names
   # ユーザーIDと行列インデックスのマッピングを作成（拡張性を考慮するよん）
    self.user_id_to_index: Dict[str, int] = {
        uid: i for i, uid in enumerate(user_ids)}
    self.user_index_to_id: Dict[int, str] = {
        i: uid for i, uid in enumerate(user_ids)}

    self.alpha_like: float = alpha_like
    self.gamma_rate: float = gamma_rate

    # 評価行列E(N×N)
    # 初期状態:各ユーザーの予算（E_ii）が1.0、他者評価（E_ij,j!i）が0.0
    self.Evaluations: np.ndarray = np.zeros(
        (self.num_users, self.numusers), dtype=float)
    np.fill_diagonal(self.Evaluations, 1.0)
    """
    [1,0,0
    0,1,0
    0,0, 1]
    みたいなことをするためのコード
    """

    # 貢献度計算用行列E'と貢献度ベクトルc（初期値はNone）
