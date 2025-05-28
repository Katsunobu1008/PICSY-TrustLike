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
    def __init__(self, user_ids: List[str], user_names: List[str], alpha_like: float, gamma_rate: float,
                 max_iterations: int = 100, tolerance: float = 1e-6):

        # ユーザー数を設定
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

    self.max_iterations: int = max_iterations
    self.tolerance: float = tolerance

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
    self.E_prime: np.ndarray = None
    self.c: np.ndarray = None

    print(f"PICSYエンジンを{self.num_users}人のユーザーで起動しました。")
    self.display_E()
    self.calculate_all_contributions()  # 初期貢献度を計算する

    def _get_user_index(self, user_id: str) -> int:
        """ユーザーIDから行列インデックスを取得する"""
        if user_id not in self/user_id_to_index:
            raise ValueError(f"ユーザーID{user_id}は存在しません。")
        return self.user_id_to_index[user_id]

    def display_E(self, title: str = "評価行列 E"):
        """評価行列を表示する"""
        print(f"\n--- {title} ---")
        # ヘッダー(To : UserA,UserB,....)
        header = "From    \\ To |"
        for i in range(self.num_users):
            header += f"{self.user_names[i]:^7} |"  # ユーザー名を7文字幅で中央揃え
        print(header)
        print("-" * (len(header)))

        # 各行を表示
        for i in range(self.num_users):
            row_str = f"{self.user_names[i]:^7} |"  # ユーザー名を7文字幅で中央揃え
            for j in range(self.num_users):
                # ^7.2fというのは何かというと、7文字幅で小数点以下2桁まで表示するという意味
                row_str += f"{self.Evaluations[i,j]:^7.2f} |"
            print(row_str)

    # 行和が1になっているか検証する
    row_sums = np.sum(self.E, axis=1)
    for i in range(self.num_users):
        if not np.isclose(row_sums[i], 1.0):
            # :{row_sums[i]:.4f}というのは、row_sums[i]を小数点以下4桁まで表示するという意味
            print(f"警告:{self.user_names[i]}の行和が1ではありません。:{row_sums[i]:.4f}")

    def display_c_vector(self, title: str = "貢献度ベクトル c"):
        if self.c_vector is None:
            print(f"\n--- {title} ---")
            print("まだ計算されていません。")
            return
        print(f"\n--- {title} ---")
        for i in range(self.num_users):
            print(f"  {self.user_names[i]:<10}: {self.c_vector[i]:.4f}")
        print(
            f"  要素の合計 (N={self.num_users} になるはず): {np.sum(self.c_vector):.4f}")

    # _calculate_E_primeメソッドの実装

    def _calculate_contribution_vector(self, E_prime_matrix: np.ndarray) -> np.ndarray:
        """
        貢献度計算用の行列E'から貢献度ベクトルcを反復計算（パワーメソッド）で計算する。
        cはE'の固有値1に対する「左」固有ベクトルを正規化したものだよん。
        """

        if E_prime_matrix.shape[0] != self.num_users or E_prime_matrix.shape[1] != self.num_users:
            # これの意味は、E_prime_matrixのサイズがユーザー数と一致していないということ
            raise ValueError(f"E'行列のサイズがユーザー数({self.num_users})と一致しません。")

        #  1.初期貢献度ベクトルc＿kの設定
        #    各ユーザーの貢献度を均等に1とし、合計がNになるようにする（PICSYの定義から。）
        #    反復計算では、合計1で正規化して計算し、最後にN倍するアプローチを取る。PICSYの定義ではそう書いてある。たしか。
        c_k = np.ones(self.num_users)

        print(f"   反復計算開始（最大{self.max_iterations}回,許容誤差:{self.tolerance}）")
        for iteration in range(self.max_iterations):
            c_k_old = c_k.copy()  # 前回の計算結果を保存するための一時変数

            # 2.反復計算式：c^(k+1)_unnormalized = c^(k) @ E'
            c_k_unnormalized = c_k_old @ E_prime_matrix

            # 3.正規化:合計がnum_usersになるようにする。
            current_sum = np.sum(c_k_unnormalized)
            if np.isclose(current_sum, 0):
                print(f"   警告（Iter{iteration+1})：貢献度の合計が0に近いため、計算を中断します。")
                # ゼロ除算を避けるため、エラーか初期値を返す。
                return np.full(self.num_users, 1.0)

            c_k = (self.num_users / current_sum)*c_k_unnormalized

            # 4.収束判定
            # 収束しているかどうかを判定するために、前回の計算結果との差を計算する。
            diff = np.sum(np.abs(c_k - c_k_old))
            if iteration % 10 == 0 or iteration == self.max_iterations - 1:  # 10回ごとと最後は状況表示
                print(
                    f"      Iter {iteration+1:3d}: diff = {diff:.2e}, c = {['{:.4f}'.format(x) for x in c_k]}")

            if diff < self.tolerance:
                print(f"    反復計算収束 (Iter {iteration+1}回, 差分 {diff:.2e})")
                return c_k
            print(f"警告: 最大反復回数 ({self.max_iterations}回) に到達しましたが、収束しませんでした。")
            print(f"     最終差分: {diff:.2e}")
            return c_k  # 収束しなくても、最終的な値を返す
