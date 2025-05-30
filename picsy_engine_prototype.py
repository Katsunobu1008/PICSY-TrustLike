import numpy as np
from typing import List, Dict, Tuple  # Python 3.8以前でも動作するようにタプルもインポート
from datetime import datetime  # いいねログのタイムスタンプ用

# --- システムのグローバル定数 ---
DEFAULT_ALPHA_LIKE = 0.05      # 「いいね」1回あたりの標準評価移転量
DEFAULT_ALPHA_LIKE_MAX = 0.3   # ユーザーが設定できるalpha_likeの上限
DEFAULT_GAMMA_RATE = 0.1       # 自然回収率
DEFAULT_MAX_ITERATIONS = 100   # 貢献度計算の最大反復回数
DEFAULT_TOLERANCE = 1e-7       # 貢献度計算の収束許容誤差


class PicsyUser:
    """
    PICSY-TrustLikeシステム内のユーザーを表すクラス。
    主にユーザーの識別情報を保持します。
    """

    def __init__(self, user_id: str, username: str):
        if not user_id:
            raise ValueError("ユーザーIDは空にできません。")
        if not username:
            raise ValueError("ユーザー名は空にできません。")
        self.user_id: str = user_id
        self.username: str = username

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

        if not user_list:
            raise ValueError("ユーザーリストが空です。最低1人以上のユーザーが必要です。")

        self.users: List[PicsyUser] = user_list
        self.num_users: int = len(self.users)

        if self.num_users == 1:
            print(
                f"警告: ユーザー数が1人のため、PICSYの評価・貢献度計算は意味を成しません。({self.users[0].username})")
        elif self.num_users < 1:
            raise ValueError("ユーザーリストが空です。")

        self.user_id_to_index: Dict[str, int] = {
            user.user_id: i for i, user in enumerate(self.users)
        }
        self.user_index_to_name: Dict[int, str] = {
            i: user.username for i, user in enumerate(self.users)
        }
        self.user_index_to_id: Dict[int, str] = {
            i: user.user_id for i, user in enumerate(self.users)
        }

        if not (0 < alpha_like_default <= alpha_like_max):
            raise ValueError(
                "alpha_like_defaultは0より大きく、alpha_like_max以下である必要があります。")
        if not (0 < alpha_like_max < 1.0):
            raise ValueError("alpha_like_maxは0より大きく1.0未満である必要があります。")
        if not (0 <= gamma_rate < 1.0):
            raise ValueError("gamma_rateは0以上1.0未満である必要があります。")

        self.alpha_like_default: float = alpha_like_default
        self.alpha_like_max: float = alpha_like_max
        self.gamma_rate: float = gamma_rate
        self.max_iterations: int = max_iterations
        self.tolerance: float = tolerance

        self.user_alpha_settings: Dict[str, float] = {
            user.user_id: self.alpha_like_default for user in self.users
        }

        self.E: np.ndarray = np.zeros(
            (self.num_users, self.num_users), dtype=float)
        if self.num_users > 0:
            np.fill_diagonal(self.E, 1.0)

        self.like_log: List[Dict] = []
        self.current_day: int = 0
        self.current_phase: str = "開始前"
        self.contribution_calculation_count: int = 0
        self.phases_to_calculate_contribution: List[str] = ["朝", "昼", "晩"]

        self.E_prime: np.ndarray = None
        self.c_vector: np.ndarray = None

        print(f"\nPICSYエンジンを{self.num_users}人のユーザーで起動しました。")
        user_name_list_str = ", ".join([user.username for user in self.users])
        print(f"  参加ユーザー: {user_name_list_str}")
        print(
            f"  デフォルトα_like: {self.alpha_like_default}, 最大α_like: {self.alpha_like_max}, γ: {self.gamma_rate}")
        print(
            f"  貢献度計算設定 - 最大反復: {self.max_iterations}, 許容誤差: {self.tolerance}")

        if self.num_users > 0:
            self.display_E(title="初期評価行列 E^(0)")
            if self.num_users > 1:
                self.calculate_all_contributions()
            else:
                print("ユーザー数が1人のため、貢献度計算はスキップされます。")
                self.c_vector = np.array([1.0])  # 1人の場合の貢献度は1
                self.display_c_vector()  # 1人の場合の貢献度も表示
        print("-" * 60)

    def _get_user_index(self, user_id: str) -> int:
        if user_id not in self.user_id_to_index:
            raise ValueError(
                f"ユーザーID'{user_id}'は存在しません。システム登録ユーザー: {list(self.user_id_to_index.keys())}")
        return self.user_id_to_index[user_id]

    def _get_user_name_from_id(self, user_id: str) -> str:
        idx = self._get_user_index(user_id)
        return self.user_index_to_name[idx]

    def display_E(self, title: str = "評価行列 E"):
        print(f"\n--- {title} ---")
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
        if self.num_users > 0:  # ユーザーがいる場合のみ行和検証
            row_sums = np.sum(self.E, axis=1)
            all_rows_sum_to_one = True
            for i in range(self.num_users):
                if not np.isclose(row_sums[i], 1.0):
                    print(f"警告:{self.user_index_to_name.get(i, f'Idx {i}')}の行和が1ではありません。:{
                          row_sums[i]:.8f}")
                    all_rows_sum_to_one = False
            if all_rows_sum_to_one:
                print("評価行列Eの全行の和はほぼ1です。")

    def display_c_vector(self, title: str = "貢献度ベクトル c"):
        # num_users=0 の場合 c_vectorは空配列でisnanはエラー
        if self.c_vector is None or (self.num_users > 0 and np.any(np.isnan(self.c_vector))):
            print(f"\n--- {title} ---")
            print("まだ有効な貢献度が計算されていません。")
            return
        if self.num_users == 0:  # ユーザーがいない場合は表示しない
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

    def _calculate_E_prime(self) -> np.ndarray:
        if self.num_users <= 1:
            return None
        diagonal_elements_E = np.diag(self.E)
        B = np.diag(diagonal_elements_E)
        D = np.ones((self.num_users, self.num_users)) - np.eye(self.num_users)
        E_prime = self.E - B + (B @ D) / (self.num_users - 1)
        return E_prime

    def _calculate_contribution_vector(self, E_prime_matrix: np.ndarray) -> np.ndarray:
        if E_prime_matrix is None or E_prime_matrix.shape[0] != self.num_users or E_prime_matrix.shape[1] != self.num_users:
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
            if (iteration + 1) % 10 == 0 or iteration == self.max_iterations - 1 or diff < self.tolerance:
                print(
                    f"      Iter {(iteration+1):3d}: diff = {diff:.3e}, c = {['{:.4f}'.format(x) for x in c_k]}")
            if diff < self.tolerance:
                print(f"    反復計算収束 (Iter {iteration+1}回, 最終差分 {diff:.3e})")
                return c_k
        print(f"警告: 最大反復回数 ({self.max_iterations}回) に到達しましたが、収束しませんでした。")
        print(f"      最終差分: {diff:.3e}")
        return c_k

    def calculate_all_contributions(self):
        print("\n>>> 貢献度計算を開始します...")
        if self.num_users == 0:
            print("ユーザーがいないため、貢献度計算は実行されません。")
            self.E_prime = np.array([])
            self.c_vector = np.array([])
            return
        if self.num_users == 1:
            print("ユーザー数が1人のため、貢献度計算は実行されません。")
            self.E_prime = None  # E' は定義できない
            self.c_vector = np.array([1.0])
            self.display_c_vector()
            return

        self.E_prime = self._calculate_E_prime()
        if self.E_prime is None:
            self.c_vector = np.full(self.num_users, np.nan)
        else:
            self.c_vector = self._calculate_contribution_vector(self.E_prime)

        if np.any(np.isnan(self.c_vector)):
            print("!!! 貢献度計算に失敗しました。")
        else:
            print("貢献度計算が完了しました。")
        self.display_c_vector()

    # --- パラメータ設定メソッド --- (ここから追加/修正)
    def set_gamma_rate(self, new_gamma: float):
        if not (0 <= new_gamma < 1.0):
            raise ValueError("gamma_rateは0以上1.0未満である必要があります。")
        self.gamma_rate = new_gamma
        print(f"パラメータ変更: 自然回収率γが {self.gamma_rate:.2f} に設定されました。")

    def set_default_alpha_like(self, new_alpha_default: float):
        if not (0 < new_alpha_default <= self.alpha_like_max):
            raise ValueError(
                f"デフォルトalpha_likeは0より大きく、最大alpha_like ({self.alpha_like_max:.2f}) 以下である必要があります。")
        old_default = self.alpha_like_default
        self.alpha_like_default = new_alpha_default
        for user_id in self.user_alpha_settings:  # self.user_alpha_settings のキーでループ
            if np.isclose(self.user_alpha_settings[user_id], old_default):
                self.user_alpha_settings[user_id] = self.alpha_like_default
        print(
            f"パラメータ変更: デフォルトalpha_likeが {self.alpha_like_default:.2f} に設定されました。")

    def set_user_alpha_like(self, user_id: str, user_alpha: float):
        idx = self._get_user_index(user_id)
        if not (0 < user_alpha <= self.alpha_like_max):
            raise ValueError(
                f"ユーザー設定alpha_likeは0より大きく、システム最大値 ({self.alpha_like_max:.2f}) 以下である必要があります。")
        self.user_alpha_settings[user_id] = user_alpha
        print(
            f"パラメータ変更: {self.user_index_to_name[idx]} のalpha_likeが {user_alpha:.2f} に設定されました。")

    def set_alpha_like_max(self, new_alpha_max: float):
        if not (0 < new_alpha_max < 1.0):
            raise ValueError("alpha_like_maxは0より大きく1.0未満である必要があります。")

        self.alpha_like_max = new_alpha_max  # 先にselfの値を更新
        if self.alpha_like_max < self.alpha_like_default:  # 更新後の値で比較
            print(
                f"警告: 新しいalpha_like_max ({self.alpha_like_max:.2f}) が現在のデフォルト値 ({self.alpha_like_default:.2f}) より小さいため、デフォルト値も更新します。")
            self.alpha_like_default = self.alpha_like_max

        for user_id in self.user_alpha_settings:
            if self.user_alpha_settings[user_id] > self.alpha_like_max:
                self.user_alpha_settings[user_id] = self.alpha_like_max
                print(
                    f"調整: {self._get_user_name_from_id(user_id)} のalpha_likeが上限値 {self.alpha_like_max:.2f} に調整されました。")
        print(f"パラメータ変更: 最大alpha_likeが {self.alpha_like_max:.2f} に設定されました。")

    # --- PICSY 動的ロジック ---
    def perform_like(self, liker_user_id: str, liked_content_creator_id: str):
        try:
            liker_idx = self._get_user_index(liker_user_id)
            liked_idx = self._get_user_index(liked_content_creator_id)

            if liker_idx == liked_idx:
                print(
                    f"情報: {self.user_index_to_name[liker_idx]} は自分自身に「いいね」できません（評価移転なし）。")
                return False

            actual_alpha_to_use = self.user_alpha_settings.get(
                liker_user_id, self.alpha_like_default)
            actual_alpha_to_use = min(actual_alpha_to_use, self.alpha_like_max)

            print(
                f"\n>>> {self.user_index_to_name[liker_idx]} が {self.user_index_to_name[liked_idx]} のコンテンツに「いいね」を実行中 (使用alpha: {actual_alpha_to_use:.3f})...")

            if self.E[liker_idx, liker_idx] >= actual_alpha_to_use:
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
                self.display_E(
                    f"「いいね」後の評価行列 E (by {self.user_index_to_name[liker_idx]})")
                if self.num_users > 1:
                    self.calculate_all_contributions()
                return True
            else:
                print(
                    f"  評価移転失敗: {self.user_index_to_name[liker_idx]} の予算不足です。")
                print(
                    f"    (現在の予算: {self.E[liker_idx, liker_idx]:.4f}, 「いいね」に必要な評価量: {actual_alpha_to_use:.3f})")
                return False
        except ValueError as e:
            print(f"エラー: 「いいね」処理中に問題が発生しました - {e}")
            return False

    def perform_natural_recovery(self):
        print(f"\n>>> 自然回収処理を実行中 (gamma = {self.gamma_rate})...")
        if self.num_users == 0:
            print("ユーザーがいないため自然回収はスキップされます。")
            return

        new_E = self.E.copy()
        for i in range(self.num_users):
            sum_others_new_row_i = 0  # この行の新しい他者評価の合計を計算
            for j in range(self.num_users):
                if i == j:
                    continue
                new_E[i, j] = (1 - self.gamma_rate) * self.E[i, j]
                sum_others_new_row_i += new_E[i, j]

            new_E[i, i] = 1.0 - sum_others_new_row_i  # 予算を行和が1になるように設定

        self.E = new_E
        print("自然回収処理が完了しました。")
        self.display_E("自然回収後の評価行列 E")
        if self.num_users > 1:
            self.calculate_all_contributions()

    # --- エンジン再初期化メソッド ---
    def reinitialize_engine(self,
                            new_user_list: List[PicsyUser],
                            alpha_like_default: float = None,
                            alpha_like_max: float = None,
                            gamma_rate: float = None,
                            max_iterations: int = None,
                            tolerance: float = None):
        print(f"\n>>> エンジンを再初期化します (新ユーザー数: {len(new_user_list)})...")

        # __init__ に処理を委譲（パラメータは None の場合、既存値を維持するロジックを __init__ 側で持つか、
        # ここで明示的に現在の値をデフォルトとして渡す）
        # ここでは、再利用性を高めるため、__init__を直接呼び出すのではなく、
        # __init__ とほぼ同じロジックをここに記述する（または、__init__を内部ヘルパーに分割する）

        # 簡潔にするため、パラメータは指定されなければ現在のエンジン設定を引き継ぐ
        current_params = {
            "alpha_like_default": self.alpha_like_default,
            "alpha_like_max": self.alpha_like_max,
            "gamma_rate": self.gamma_rate,
            "max_iterations": self.max_iterations,
            "tolerance": self.tolerance
        }
        if alpha_like_default is not None:
            current_params["alpha_like_default"] = alpha_like_default
        if alpha_like_max is not None:
            current_params["alpha_like_max"] = alpha_like_max
        if gamma_rate is not None:
            current_params["gamma_rate"] = gamma_rate
        if max_iterations is not None:
            current_params["max_iterations"] = max_iterations
        if tolerance is not None:
            current_params["tolerance"] = tolerance

        # 新しいインスタンスを作るかのように、selfの属性を再設定
        self.__init__(  # 自分自身の__init__を再度呼び出すことでリセット
            user_list=new_user_list,
            alpha_like_default=current_params["alpha_like_default"],
            alpha_like_max=current_params["alpha_like_max"],
            gamma_rate=current_params["gamma_rate"],
            max_iterations=current_params["max_iterations"],
            tolerance=current_params["tolerance"]
        )
        print(f"エンジンが新ユーザー構成で再初期化されました。")

    # --- 状態取得・表示メソッド群 --- (ここから追加/修正)

    def get_user_budget(self, user_id: str) -> float:
        idx = self._get_user_index(user_id)
        return self.E[idx, idx]

    def get_user_contribution(self, user_id: str) -> float:
        if self.c_vector is None or (self.num_users > 0 and np.any(np.isnan(self.c_vector))):
            return np.nan if self.num_users > 0 else 0.0  # ユーザー0なら貢献度も0
        idx = self._get_user_index(user_id)
        # ユーザー数が1でc_vectorが[1.0]のような場合、idxが0以外だとエラーになるのでチェック
        if idx < len(self.c_vector):
            return self.c_vector[idx]
        return np.nan  # インデックス範囲外の場合 (基本的には起こらないはず)

    def get_user_purchasing_power(self, user_id: str) -> float:
        budget = self.get_user_budget(user_id)
        contribution = self.get_user_contribution(user_id)
        if np.isnan(budget) or np.isnan(contribution):
            return np.nan
        return budget * contribution

    def get_user_status(self, user_id: str) -> Dict:
        idx = self._get_user_index(user_id)
        username = self.user_index_to_name[idx]
        contribution = self.get_user_contribution(user_id)
        budget = self.get_user_budget(user_id)
        purchasing_power = self.get_user_purchasing_power(user_id)

        return {
            "id": user_id,
            "name": username,
            "contribution": contribution if not np.isnan(contribution) else "N/A",
            "budget": budget,
            "purchasing_power": purchasing_power if not np.isnan(purchasing_power) else "N/A"
        }

    def display_all_user_status(self):
        print("\n--- 全ユーザーステータス ---")
        if self.num_users == 0:
            print("ユーザーがいません。")
            return

        header = f"{'ID':<10} | {'名前':<10} | {'貢献度':^10} | {'予算':^10} | {'購買力':^10}"
        print(header)
        print("-" * len(header))
        for user_obj in self.users:  # self.users リストをループ
            status = self.get_user_status(user_obj.user_id)
            cont_str = f"{status['contribution']:.4f}" if isinstance(
                status['contribution'], float) else status['contribution']
            purch_str = f"{status['purchasing_power']:.4f}" if isinstance(
                status['purchasing_power'], float) else status['purchasing_power']
            print(
                f"{status['id']:<10} | {status['name']:<10} | {cont_str:^10} | {status['budget']:^10.4f} | {purch_str:^10}")

    def display_like_log(self):
        print("\n--- いいね履歴 (最新10件) ---")
        if not self.like_log:
            print("まだ「いいね」の履歴はありません。")
            return

        for log_entry in reversed(self.like_log[-10:]):
            timestamp_str = log_entry['timestamp'].strftime(
                '%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp_str}] {log_entry['liker_name']} ({log_entry['liker_id']}) "
                  f"-> {log_entry['liked_creator_name']} ({log_entry['liked_creator_id']}) "
                  f"| α={log_entry['alpha_used']:.3f}")
        if len(self.like_log) > 10:
            print(f"...他{len(self.like_log)-10}件")

    def display_system_status(self):
        print("\n--- システム状況 ---")
        print(f"  経過日数: {self.current_day} 日目")
        print(f"  現在のフェーズ: {self.current_phase}")
        print(f"  貢献度計算回数（通算）: {self.contribution_calculation_count}")
        print(f"  デフォルトα_like: {self.alpha_like_default:.3f}")
        print(f"  最大α_like: {self.alpha_like_max:.3f}")
        print(f"  自然回収率γ: {self.gamma_rate:.3f}")
        print(f"  貢献度計算タイミング: {self.phases_to_calculate_contribution}")

    def advance_phase(self):
        phases = ["朝", "昼", "晩"]
        if self.current_phase == "開始前" or self.num_users == 0:  # ユーザー0人の時は進めない
            if self.num_users > 0:
                self.current_phase = "朝"
                self.current_day = 1
            else:  # ユーザーがいない場合は何もしない
                print("ユーザーがいないためフェーズを進行できません。")
                return

        else:
            current_phase_idx = phases.index(self.current_phase)
            next_phase_idx = (current_phase_idx + 1) % 3
            self.current_phase = phases[next_phase_idx]
            if next_phase_idx == 0:
                self.current_day += 1

        print(f"\n=== {self.current_day}日目 - {self.current_phase} ===")
        self.display_system_status()

        if self.current_phase in self.phases_to_calculate_contribution:
            if self.num_users > 1:
                self.calculate_all_contributions()
                self.contribution_calculation_count += 1

        if self.current_phase == "晩":
            self.perform_natural_recovery()


# (メイン実行ブロックは前回と同様なので省略。上記の修正済みクラスを使ってテストしてください)
# --- メイン実行ブロック ---
if __name__ == "__main__":
    print("PICSY-TrustLike エンジンプロトタイプへようこそ！")

    # 初期ユーザーリスト
    initial_users = [
        PicsyUser(user_id="u001", username="Alice"),
        PicsyUser(user_id="u002", username="Bob"),
        PicsyUser(user_id="u003", username="Charlie")
    ]

    # PicsyEngine のインスタンスを作成
    engine = PicsyEngine(
        user_list=initial_users,
        alpha_like_default=DEFAULT_ALPHA_LIKE,
        alpha_like_max=DEFAULT_ALPHA_LIKE_MAX,
        gamma_rate=DEFAULT_GAMMA_RATE,
        max_iterations=50,
        tolerance=1e-6
    )
    engine.phases_to_calculate_contribution = ["晩"]

    print("\n" + "="*10 + " シミュレーション開始 " + "="*10)

    # --- 1日目 ---
    engine.advance_phase()  # 1日目 朝
    engine.perform_like(liker_user_id="u001", liked_content_creator_id="u002")
    engine.perform_like(liker_user_id="u001", liked_content_creator_id="u002")
    engine.display_all_user_status()
    engine.display_like_log()

    engine.advance_phase()  # 1日目 昼
    engine.perform_like(liker_user_id="u002", liked_content_creator_id="u003")
    engine.display_all_user_status()

    engine.advance_phase()  # 1日目 晩
    engine.perform_like(liker_user_id="u003", liked_content_creator_id="u001")
    engine.display_all_user_status()

    # --- 2日目 ---
    engine.advance_phase()  # 2日目 朝
    try:
        engine.set_user_alpha_like(user_id="u001", user_alpha=0.1)
    except ValueError as e:
        print(f"設定エラー: {e}")
    # print(f"Aliceの現在のα_like設定: {engine.user_alpha_settings['u001']}") # エラーになる可能性を考慮
    if 'u001' in engine.user_alpha_settings:
        print(f"Aliceの現在のα_like設定: {engine.user_alpha_settings['u001']}")
    engine.perform_like(liker_user_id="u001", liked_content_creator_id="u003")
    engine.display_all_user_status()

    engine.advance_phase()  # 2日目 昼
    engine.advance_phase()  # 2日目 晩
    engine.display_all_user_status()
    engine.display_like_log()

    print("\n\n" + "="*10 + " エンジン再初期化テスト (5ユーザー) " + "="*10)
    new_users_for_reinit = [
        PicsyUser(user_id=f"nu{i:03}", username=f"NewUser{i}") for i in range(5)
    ]
    engine.reinitialize_engine(
        new_user_list=new_users_for_reinit,
        alpha_like_default=0.03,
        gamma_rate=0.05
    )
    engine.phases_to_calculate_contribution = ["昼", "晩"]

    engine.advance_phase()
    engine.perform_like("nu000", "nu001")
    engine.perform_like("nu000", "nu002")
    engine.perform_like("nu001", "nu000")
    engine.display_all_user_status()

    engine.advance_phase()
    engine.display_all_user_status()

    engine.advance_phase()
    engine.display_all_user_status()
    engine.display_like_log()

    print("\n" + "="*10 + " ユーザー0人テスト " + "="*10)
    engine_zero_user = PicsyEngine(
        user_list=[], alpha_like_default=0.01, alpha_like_max=0.1, gamma_rate=0.01)
    engine_zero_user.advance_phase()  # 何も起こらないはず
    engine_zero_user.display_all_user_status()

    print("\n" + "="*10 + " ユーザー1人テスト " + "="*10)
    engine_one_user = PicsyEngine(user_list=[PicsyUser(
        "single001", " एकल")], alpha_like_default=0.01, alpha_like_max=0.1, gamma_rate=0.01)
    engine_one_user.advance_phase()
    # 1人なのでいいねはできない
    # engine_one_user.perform_like("single001", "single001") # エラーまたは情報メッセージ
    engine_one_user.display_all_user_status()

    print("\n" + "="*10 + " シミュレーション終了 " + "="*10)
