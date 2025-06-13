import numpy as np
from typing import List, Dict, Tuple
from datetime import datetime

# --- システムのグローバル定数 (デフォルト値として使用) ---
DEFAULT_ALPHA_LIKE = 0.05      # 「いいね」1回あたりの標準評価移転量
DEFAULT_ALPHA_LIKE_MAX = 0.3   # ユーザーが設定できるalpha_likeの上限
DEFAULT_GAMMA_RATE = 0.1       # 自然回収率
DEFAULT_MAX_ITERATIONS = 100   # 貢献度計算の最大反復回数
DEFAULT_TOLERANCE = 1e-7       # 貢献度計算の収束許容誤差

# ==============================================================================
# 1. PicsyUser クラス: ユーザー情報を保持するデータクラス
# ==============================================================================


class PicsyUser:
    """
    PICSY-TrustLikeシステム内のユーザーを表すクラス。
    主にユーザーの識別情報を保持します。評価情報のような動的な状態はPicsyEngineが一元管理します。
    """

    def __init__(self, user_id: str, username: str):
        """
        PicsyUserオブジェクトを初期化します。
        Args:
            user_id (str): ユーザーの一意なID。
            username (str): ユーザーの表示名。
        """
        if not user_id or not username:
            raise ValueError("ユーザーIDとユーザー名は空にできません。")
        self.user_id: str = user_id
        self.username: str = username

    def __repr__(self) -> str:
        """オブジェクトを分かりやすい文字列で表現します。print()などで使われます。"""
        return f"PicsyUser(user_id='{self.user_id}', username='{self.username}')"

    def __eq__(self, other) -> bool:
        """2つのPicsyUserオブジェクトが等しいか（user_idが同じか）を比較します。"""
        if isinstance(other, PicsyUser):
            return self.user_id == other.user_id
        return False

    def __hash__(self) -> int:
        """オブジェクトを辞書のキーとして使う場合などに必要なハッシュ値を返します。"""
        return hash(self.user_id)

# ==============================================================================
# 2. PicsyEngine クラス: PICSYのコアロジックを管理・実行する中心的なクラス
# ==============================================================================


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

        # --- 属性の初期化 ---
        self.users: List[PicsyUser] = []
        self.num_users: int = 0
        self.user_id_to_index: Dict[str, int] = {}
        self.user_index_to_name: Dict[int, str] = {}
        self.user_index_to_id: Dict[int, str] = {}
        self.user_alpha_settings: Dict[str, float] = {}
        self.E: np.ndarray = np.array([])
        self.E_prime: np.ndarray = None
        self.c_vector: np.ndarray = None
        self.like_log: List[Dict] = []
        self.current_day: int = 0
        self.current_phase: str = "開始前"
        self.contribution_calculation_count: int = 0

        # --- 初期化処理の実行 ---
        # reinitialize_engineメソッドを呼び出すことで、初期化処理を共通化
        self.reinitialize_engine(
            new_user_list=user_list,
            alpha_like_default=alpha_like_default,
            alpha_like_max=alpha_like_max,
            gamma_rate=gamma_rate,
            max_iterations=max_iterations,
            tolerance=tolerance
        )

    # --- ヘルパーメソッド ---
    def _get_user_index(self, user_id: str) -> int:
        """ユーザーIDから行列インデックスを安全に取得する。"""
        if user_id not in self.user_id_to_index:
            raise ValueError(
                f"ユーザーID'{user_id}'は存在しません。システム登録ユーザー: {list(self.user_id_to_index.keys())}")
        return self.user_id_to_index[user_id]

    def _get_user_name_from_id(self, user_id: str) -> str:
        """ユーザーIDからユーザー名を安全に取得する。"""
        idx = self._get_user_index(user_id)
        return self.user_index_to_name[idx]

    # --- 表示用メソッド ---
    def display_E(self, title: str = "評価行列 E"):
        """評価行列Eを整形して表示する。"""
        print(f"\n--- {title} ---")
        if self.num_users == 0:
            print("ユーザーがいません。")
            return

        header = "From      \\ To |"
        for i in range(self.num_users):
            header += f" {self.user_index_to_name.get(i, f'Idx {i}'):^7} |"
        print(header)
        print("-" * (len(header)))

        for i in range(self.num_users):
            row_str = f"{self.user_index_to_name.get(i, f'Idx {i}'):<9} |"
            for j in range(self.num_users):
                row_str += f"{self.E[i, j]:^7.4f} |"
            print(row_str)
        print("-" * (len(header)))

        row_sums = np.sum(self.E, axis=1)
        if np.allclose(row_sums, 1.0):
            print("評価行列Eの全行の和はほぼ1です。")
        else:
            for i in range(self.num_users):
                if not np.isclose(row_sums[i], 1.0):
                    print(f"警告:{self.user_index_to_name.get(i, f'Idx {i}')}の行和が1ではありません。:{
                          row_sums[i]:.8f}")

    def display_c_vector(self, title: str = "貢献度ベクトル c"):
        """貢献度ベクトルcを整形して表示する。"""
        if self.c_vector is None or (self.num_users > 0 and np.any(np.isnan(self.c_vector))):
            print(f"\n--- {title} ---")
            print("まだ有効な貢献度が計算されていません。")
            return
        if self.num_users == 0:
            print(f"\n--- {title} ---")
            print("ユーザーがいません。")
            return

        print(f"\n--- {title} ---")
        for i in range(self.num_users):
            print(f"  {self.user_index_to_name.get(i, f'Idx {i}'):<10}: {
                  self.c_vector[i]:.4f}")
        if self.num_users > 0:
            print(
                f"  要素の合計 (N={self.num_users} になるはず): {np.sum(self.c_vector):.4f}")

    # --- PICSY コア計算ロジック ---
    def _calculate_E_prime(self) -> np.ndarray:
        """現在の評価行列 E から貢献度計算用行列 E' を計算する。"""
        if self.num_users <= 1:
            return None
        diagonal_elements_E = np.diag(self.E)
        B = np.diag(diagonal_elements_E)
        D = np.ones((self.num_users, self.num_users)) - np.eye(self.num_users)
        E_prime = self.E - B + (B @ D) / (self.num_users - 1)
        return E_prime

    def _calculate_contribution_vector(self, E_prime_matrix: np.ndarray) -> np.ndarray:
        """E' から貢献度ベクトル c を反復計算（パワーメソッド）で計算する。"""
        if E_prime_matrix is None:
            return np.full(self.num_users, np.nan) if self.num_users > 0 else np.array([])

        c_k = np.ones(self.num_users)
        for iteration in range(self.max_iterations):
            c_k_old = c_k.copy()
            c_k_unnormalized = c_k_old @ E_prime_matrix
            current_sum = np.sum(c_k_unnormalized)

            if np.isclose(current_sum, 0):
                print(f"      警告(Iter {iteration+1}): 貢献度の合計が0に近いため、計算を中断します。")
                return np.full(self.num_users, np.nan)

            c_k = (self.num_users / current_sum) * c_k_unnormalized
            diff = np.sum(np.abs(c_k - c_k_old))

            if diff < self.tolerance:
                print(f"    反復計算収束 (Iter {iteration+1}回, 最終差分 {diff:.3e})")
                return c_k

        print(
            f"警告: 最大反復回数 ({self.max_iterations}回) に到達しましたが、収束しませんでした。最終差分: {diff:.3e}")
        return c_k

    def calculate_all_contributions(self):
        """現在の評価行列Eに基づいて、全ユーザーの貢献度cを計算・更新する。"""
        print("\n>>> 貢献度計算を開始します...")
        if self.num_users <= 1:
            print("ユーザー数が1人のため、貢献度計算は実行されません。")
            self.E_prime = None
            self.c_vector = np.array(
                [1.0]) if self.num_users == 1 else np.array([])
            self.display_c_vector()
            return

        self.E_prime = self._calculate_E_prime()
        self.c_vector = self._calculate_contribution_vector(self.E_prime)

        if np.any(np.isnan(self.c_vector)):
            print("!!! 貢献度計算に失敗しました。")
        else:
            print("貢献度計算が完了しました。")
        self.display_c_vector()

    # --- パラメータ設定メソッド ---
    def set_gamma_rate(self, new_gamma: float):
        """自然回収率γを設定する。"""
        if not (0 <= new_gamma < 1.0):
            raise ValueError("gamma_rateは0以上1.0未満である必要があります。")
        self.gamma_rate = new_gamma
        print(f"パラメータ変更: 自然回収率γが {self.gamma_rate:.2f} に設定されました。")

    def set_user_alpha_like(self, user_id: str, user_alpha: float):
        """特定のユーザーの「1いいね」あたりの評価量を設定する。"""
        idx = self._get_user_index(user_id)
        if not (0 < user_alpha <= self.alpha_like_max):
            raise ValueError(
                f"ユーザー設定alpha_likeは0より大きく、システム最大値 ({self.alpha_like_max:.2f}) 以下である必要があります。")
        self.user_alpha_settings[user_id] = user_alpha
        print(
            f"パラメータ変更: {self.user_index_to_name[idx]} のalpha_likeが {user_alpha:.2f} に設定されました。")

    # --- PICSY 動的ロジック ---
    def perform_like(self, liker_user_id: str, liked_content_creator_id: str):
        """「いいね」による評価移転（取引）を実行し、貢献度を再計算する。"""
        try:
            liker_idx = self._get_user_index(liker_user_id)
            liked_idx = self._get_user_index(liked_content_creator_id)

            if liker_idx == liked_idx:
                print(
                    f"情報: {self.user_index_to_name[liker_idx]} は自分自身に「いいね」できません。")
                return False

            actual_alpha_to_use = self.user_alpha_settings.get(
                liker_user_id, self.alpha_like_default)
            actual_alpha_to_use = min(actual_alpha_to_use, self.alpha_like_max)

            print(
                f"\n>>> {self.user_index_to_name[liker_idx]} が {self.user_index_to_name[liked_idx]} に「いいね」を実行 (使用α: {actual_alpha_to_use:.3f})...")

            if self.E[liker_idx, liker_idx] >= actual_alpha_to_use:
                # いいねログに記録
                log_entry = {
                    "timestamp": datetime.now(),
                    "liker_id": liker_user_id,
                    "liker_name": self.user_index_to_name[liker_idx],
                    "liked_creator_id": liked_content_creator_id,
                    "liked_creator_name": self.user_index_to_name[liked_idx],
                    "alpha_used": actual_alpha_to_use
                }
                self.like_log.append(log_entry)

                self.E[liker_idx, liker_idx] -= actual_alpha_to_use
                self.E[liker_idx, liked_idx] += actual_alpha_to_use
                print(f"  評価移転成功: {actual_alpha_to_use:.3f} ポイント。")

                if self.num_users > 1:
                    self.calculate_all_contributions()
                return True
            else:
                print(
                    f"  評価移転失敗: {self.user_index_to_name[liker_idx]} の予算不足です。")
                print(
                    f"    (現在の予算: {self.E[liker_idx, liker_idx]:.4f}, 必要量: {actual_alpha_to_use:.3f})")
                return False
        except ValueError as e:
            print(f"エラー: 「いいね」処理中に問題が発生しました - {e}")
            return False

    def perform_natural_recovery(self):
        """全ユーザーに対して自然回収を実行し、貢献度を再計算する。"""
        print(f"\n>>> 自然回収処理を実行中 (gamma = {self.gamma_rate})...")
        if self.num_users == 0:
            print("ユーザーがいないため自然回収はスキップされます。")
            return

        new_E = self.E.copy()
        for i in range(self.num_users):
            sum_others_new_row_i = 0
            for j in range(self.num_users):
                if i == j:
                    continue
                new_E[i, j] = (1 - self.gamma_rate) * self.E[i, j]
                sum_others_new_row_i += new_E[i, j]

            new_E[i, i] = 1.0 - sum_others_new_row_i

        self.E = new_E
        print("自然回収処理が完了しました。")
        self.display_E("自然回収後の評価行列 E")
        if self.num_users > 1:
            self.calculate_all_contributions()

    # --- その他、エンジン管理用メソッド ---
    def reinitialize_engine(self, new_user_list: List[PicsyUser], **kwargs):
        """エンジンを新しいユーザーリストとパラメータで再初期化する。"""
        print(f"\n>>> エンジンを再初期化します (新ユーザー数: {len(new_user_list)})...")
        # kwargsからパラメータを取得、なければ現在の値を引き継ぐ
        params = {
            "alpha_like_default": kwargs.get("alpha_like_default", self.alpha_like_default),
            "alpha_like_max": kwargs.get("alpha_like_max", self.alpha_like_max),
            "gamma_rate": kwargs.get("gamma_rate", self.gamma_rate),
            "max_iterations": kwargs.get("max_iterations", self.max_iterations),
            "tolerance": kwargs.get("tolerance", self.tolerance)
        }
        self.__init__(user_list=new_user_list, **params)
        print("エンジンが新ユーザー構成で再初期化されました。")

    def advance_phase(self):
        """システムの日付とフェーズを進行させ、必要な処理をトリガーする。"""
        # ... (前回の回答で実装した通り) ...

    def display_all_user_status(self):
        """全ユーザーのステータス（貢献度、予算、購買力）を表示する。"""
        # ... (前回の回答で実装した通り) ...

    def display_like_log(self):
        """いいねの履歴を表示する。"""
        # ... (前回の回答で実装した通り) ...

# メイン実行ブロックは長くなるので、別ファイルに分けるか、この下に記述します。
# 今回はここに記述します。


if __name__ == "__main__":
    # (前回の回答で作成した、詳細なテストシナリオを含むメイン実行ブロックをここに記述)
    pass
