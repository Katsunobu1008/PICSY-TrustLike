import numpy as np
from typing import List, Tuple, Dict  # Python 3.8以前でも動作するように

# ---システムの基本設計---

ALPHA_LIKE = 0.05  # 「いいね」一回あたりの標準評価移転料
GAMMA_RATE = 0.1   # 自然回収率 (前回のシミュレーションに合わせ0.1に変更)


class PicsyUser:  # 修正: シンプルなデータクラスとして役割を明確化
    def __init__(self, user_id: str, username: str):  # num_total_users は不要に
        self.user_id: str = user_id
        self.username: str = username
        # evaluations は PicsyEngine が一元管理するため、ここでは持たない

    def __repr__(self) -> str:
        return f"PicsyUser(user_id='{self.user_id}', username='{self.username}')"


class PicsyEngine:
    def __init__(self, user_list: List[PicsyUser],  # PicsyUserオブジェクトのリストを受け取るように変更
                 alpha_like: float, gamma_rate: float,
                 max_iterations: int = 100, tolerance: float = 1e-7):  # toleranceを少し厳しく

        self.users: List[PicsyUser] = user_list  # ユーザーオブジェクトのリストを保持
        self.num_users: int = len(self.users)
        if self.num_users <= 1:
            raise ValueError("ユーザー数が1以下です。ユーザー数は2以上である必要があります。")

        # ユーザーIDと行列インデックスのマッピングを作成（拡張性を考慮するよん）
        self.user_id_to_index: Dict[str, int] = {
            user.user_id: i for i, user in enumerate(self.users)}
        # ユーザー名も辞書で保持しておくと表示時に便利 (オプション)
        self.user_index_to_name: Dict[int, str] = {
            i: user.username for i, user in enumerate(self.users)}

        self.alpha_like: float = alpha_like
        self.gamma_rate: float = gamma_rate

        self.max_iterations: int = max_iterations
        self.tolerance: float = tolerance

        # 評価行列E(N×N)
        # 初期状態:各ユーザーの予算（E_ii）が1.0、他者評価（E_ij,j!=i）が0.0
        self.E: np.ndarray = np.zeros(  # 修正: 属性名を E に統一
            # 修正: タイポ numusers -> num_users
            (self.num_users, self.num_users), dtype=float)
        np.fill_diagonal(self.E, 1.0)
        """
        [1,0,0
         0,1,0
         0,0,1]
        みたいなことをするためのコード
        """

        # 貢献度計算用行列E'と貢献度ベクトルc（初期値はNone）
        self.E_prime: np.ndarray = None
        self.c_vector: np.ndarray = None  # 修正: c_vector に統一

        print(f"PICSYエンジンを{self.num_users}人のユーザーで起動しました。")
        # ユーザー名も表示
        user_name_list_str = ", ".join([user.username for user in self.users])
        print(f"  参加ユーザー: {user_name_list_str}")
        print(f"  最大反復回数: {self.max_iterations}, 許容誤差: {self.tolerance}")
        self.display_E()
        self.calculate_all_contributions()  # 初期貢献度を計算する

    def _get_user_index(self, user_id: str) -> int:
        """ユーザーIDから行列インデックスを取得する"""
        if user_id not in self.user_id_to_index:  # 修正: self.user_id_to_index
            raise ValueError(f"ユーザーID'{user_id}'は存在しません。")
        return self.user_id_to_index[user_id]

    def display_E(self, title: str = "評価行列 E"):
        """評価行列を表示する"""
        print(f"\n--- {title} ---")
        # ヘッダー(To : UserA,UserB,....)
        header = "From      \\ To |"  # Fromの幅を調整
        for i in range(self.num_users):
            header += f" {self.user_index_to_name[i]:^7} |"  # ユーザー名を7文字幅で中央揃え
        print(header)
        print("-" * (len(header)))

        # 各行を表示
        for i in range(self.num_users):
            row_str = f"{self.user_index_to_name[i]:<9} |"  # ユーザー名を9文字幅で左揃え
            for j in range(self.num_users):
                # ^7.4fというのは何かというと、7文字幅で小数点以下4桁まで表示するという意味 (修正: .2f -> .4f)
                # 修正: self.Evaluations -> self.E
                row_str += f"{self.E[i, j]:^7.4f} |"
            print(row_str)
        print("-" * (len(header)))

        # 行和が1になっているか検証する
        row_sums = np.sum(self.E, axis=1)  # 修正: self.Evaluations -> self.E
        all_rows_sum_to_one = True
        for i in range(self.num_users):
            if not np.isclose(row_sums[i], 1.0):
                # :{row_sums[i]:.4f}というのは、row_sums[i]を小数点以下4桁まで表示するという意味
                print(
                    f"警告:{self.user_index_to_name[i]}の行和が1ではありません。:{row_sums[i]:.8f}")
                all_rows_sum_to_one = False
        if all_rows_sum_to_one:
            print("評価行列Eの全行の和はほぼ1です。")

    def display_c_vector(self, title: str = "貢献度ベクトル c"):
        if self.c_vector is None:
            print(f"\n--- {title} ---")
            print("まだ計算されていません。")
            return
        print(f"\n--- {title} ---")
        for i in range(self.num_users):
            # 修正: user_names -> user_index_to_name
            print(
                f"  {self.user_index_to_name[i]:<10}: {self.c_vector[i]:.4f}")
        print(
            f"  要素の合計 (N={self.num_users} になるはず): {np.sum(self.c_vector):.4f}")

    # --- PICSY コア計算ロジック ---
    def _calculate_E_prime(self) -> np.ndarray:  # 実装追加
        """
        現在の評価行列 self.E から貢献度計算用行列 E' を計算する。
        E' = E - B + (B @ D) / (N - 1)
        """
        if self.num_users <= 1:
            raise ValueError("ユーザー数は2以上である必要があります。")

        diagonal_elements_E = np.diag(self.E)
        B = np.diag(diagonal_elements_E)
        D = np.ones((self.num_users, self.num_users)) - np.eye(self.num_users)

        E_prime = self.E - B + (B @ D) / (self.num_users - 1)
        return E_prime

    def _calculate_contribution_vector(self, E_prime_matrix: np.ndarray) -> np.ndarray:
        """
        貢献度計算用の行列E'から貢献度ベクトルcを反復計算（パワーメソッド）で計算する。
        cはE'の固有値1に対する「左」固有ベクトルを正規化したものだよん。
        """

        if E_prime_matrix.shape[0] != self.num_users or E_prime_matrix.shape[1] != self.num_users:
            # これの意味は、E_prime_matrixのサイズがユーザー数と一致していないということ
            raise ValueError(f"E'行列のサイズがユーザー数({self.num_users})と一致しません。")

        #  1.初期貢献度ベクトルc＿kの設定
        #     各ユーザーの貢献度を均等に1とし、合計がNになるようにする（PICSYの定義から。）
        #     反復計算では、合計1で正規化して計算し、最後にN倍するアプローチを取る。PICSYの定義ではそう書いてある。たしか。
        #     -> PICSYの定義では c_i の合計が N。なので初期値は各要素1で合計Nで良い。
        c_k = np.ones(self.num_users)

        # print(f"    反復計算開始（最大{self.max_iterations}回,許容誤差:{self.tolerance}）") # calculate_all_contributions に移動
        for iteration in range(self.max_iterations):
            c_k_old = c_k.copy()  # 前回の計算結果を保存するための一時変数

            # 2.反復計算式：c^(k+1)_unnormalized = c^(k) @ E'
            #   c_k は行ベクトルとして扱う（NumPyの1D配列は適切に処理される）
            c_k_unnormalized = c_k_old @ E_prime_matrix

            # 3.正規化:合計がnum_usersになるようにする。
            current_sum = np.sum(c_k_unnormalized)
            if np.isclose(current_sum, 0):
                print(f"      警告(Iter {iteration+1}): 貢献度の合計が0に近いため、計算を中断します。")
                # ゼロ除算を避けるため、エラーか初期値を返す。
                # ここでは、問題があることを示すためにNaNを含む配列を返す
                return np.full(self.num_users, np.nan)

            c_k = (self.num_users / current_sum) * c_k_unnormalized

            # 4.収束判定
            # 収束しているかどうかを判定するために、前回の計算結果との差を計算する。
            diff = np.sum(np.abs(c_k - c_k_old))  # L1ノルム
            if (iteration + 1) % 10 == 0 or iteration == self.max_iterations - 1 or diff < self.tolerance:  # 10回ごと、最後、収束時に状況表示
                print(
                    f"      Iter {(iteration+1):3d}: diff = {diff:.3e}, c = {['{:.4f}'.format(x) for x in c_k]}")

            if diff < self.tolerance:
                print(f"    反復計算収束 (Iter {iteration+1}回, 最終差分 {diff:.3e})")
                return c_k

        # ループを抜けた場合（最大反復回数に到達）
        print(f"警告: 最大反復回数 ({self.max_iterations}回) に到達しましたが、収束しませんでした。")
        print(f"      最終差分: {diff:.3e}")
        return c_k  # 収束しなくても、最終的な値を返す

    def calculate_all_contributions(self):
        """
        現在の評価行列 E に基づいて、全てのユーザーの貢献度 c を計算し、
        self.E_prime と self.c_vector を更新する。
        """
        print("\n>>> 貢献度計算を開始します...")
        self.E_prime = self._calculate_E_prime()
        # print("   計算された E':") # デバッグ用に表示しても良い
        # print(self.E_prime)
        self.c_vector = self._calculate_contribution_vector(self.E_prime)

        if np.any(np.isnan(self.c_vector)):
            print("!!! 貢献度計算に失敗しました。以前の貢献度を維持します（もしあれば）。")
        else:
            print("貢献度計算が完了しました。")
        self.display_c_vector()

    # --- PICSY 動的ロジック ---
    def perform_like(self, liker_user_id: str, liked_content_creator_id: str):
        """
        指定されたユーザー間で「いいね」による評価移転（取引）を実行する。
        その後、貢献度を再計算する。
        """
        try:
            liker_idx = self._get_user_index(liker_user_id)
            liked_idx = self._get_user_index(liked_content_creator_id)

            if liker_idx == liked_idx:
                print(
                    f"情報: {self.user_index_to_name[liker_idx]} は自分自身に「いいね」できません（評価移転なし）。")
                return False  # 取引は行われなかった

            print(
                f"\n>>> {self.user_index_to_name[liker_idx]} が {self.user_index_to_name[liked_idx]} のコンテンツに「いいね」を実行中...")

            if self.E[liker_idx, liker_idx] >= self.alpha_like:
                # トランザクションの記録（将来の機能）
                # self.transaction_log.append(...)
                # print(f"  いいね前: {USER_NAMES[liker_idx]} 予算={self.E[liker_idx, liker_idx]:.4f}, {USER_NAMES[liker_idx]}->{USER_NAMES[liked_idx]}評価={self.E[liker_idx, liked_idx]:.4f}")

                self.E[liker_idx, liker_idx] -= self.alpha_like  # 予算(E_ii)を減らす
                # 対象者への評価(E_iS)を増やす
                self.E[liker_idx, liked_idx] += self.alpha_like

                # print(f"  いいね後: {USER_NAMES[liker_idx]} 予算={self.E[liker_idx, liker_idx]:.4f}, {USER_NAMES[liker_idx]}->{USER_NAMES[liked_idx]}評価={self.E[liker_idx, liked_idx]:.4f}")
                print(f"  評価移転成功: {self.alpha_like:.2f} ポイント。")
                self.display_E(
                    f"「いいね」後の評価行列 E (by {self.user_index_to_name[liker_idx]})")

                # 「いいね」の都度、貢献度を再計算
                self.calculate_all_contributions()
                return True  # 取引成功
            else:
                print(
                    f"  評価移転失敗: {self.user_index_to_name[liker_idx]} の予算不足です。")
                print(
                    f"    (現在の予算: {self.E[liker_idx, liker_idx]:.4f}, 「いいね」に必要な評価量: {self.alpha_like:.2f})")
                return False  # 取引失敗
        except ValueError as e:
            print(f"エラー: 「いいね」処理中に問題が発生しました - {e}")
            return False

    def perform_natural_recovery(self):
        """
        全ユーザーに対して自然回収を実行し、評価行列 E を更新する。
        その後、貢献度を再計算する。
        """
        print(f"\n>>> 自然回収処理を実行中 (gamma = {self.gamma_rate})...")

        # Eを直接変更するとループ内で問題が起きる可能性があるため、コピーを操作する
        new_E = self.E.copy()
        for i in range(self.num_users):
            # 他者への評価 E_ij (j!=i) を減衰させる
            for j in range(self.num_users):
                if i == j:
                    continue
                new_E[i, j] = (1 - self.gamma_rate) * self.E[i, j]  # 元のEから計算

            # 予算 E_ii を、行和が1になるように設定
            # E_ii_new = 1.0 - sum(new_E[i,j] for j!=i)
            # new_E[i,i]はまだ古い値なのでこれでOK
            sum_others_new = np.sum(new_E[i, :]) - new_E[i, i]
            new_E[i, i] = 1.0 - sum_others_new

        self.E = new_E  # 計算後の行列で置き換え
        print("自然回収処理が完了しました。")
        self.display_E("自然回収後の評価行列 E")

        # 自然回収後、貢献度を再計算
        self.calculate_all_contributions()


# --- メイン実行ブロック ---
if __name__ == "__main__":
    print("PICSY-TrustLike エンジンプロトタイプへようこそ！")

    # ユーザー情報を定義 (PicsyUserオブジェクトのリストとして)
    users_global = [
        PicsyUser(user_id="u001", username="Alice"),
        PicsyUser(user_id="u002", username="Bob"),
        PicsyUser(user_id="u003", username="Charlie")
    ]

    # PicsyEngine のインスタンスを作成
    engine = PicsyEngine(
        user_list=users_global,  # PicsyUserオブジェクトのリストを渡す
        alpha_like=ALPHA_LIKE,
        gamma_rate=GAMMA_RATE,
        max_iterations=200,
        tolerance=1e-7
    )

    # --- シミュレーションシナリオ ---
 print("\n=== シミュレーション開始 ===")

    # イベント1: Alice が Bob のコンテンツに「いいね」
    print("\n--- イベント1: Alice (u001) が Bob (u002) に「いいね」 ---")
    engine.perform_like(liker_user_id="u001", liked_content_creator_id="u002")

    # イベント2: Alice (u001) が Charlie (u003) のコンテンツに「いいね」
    print("\n--- イベント2: Alice (u001) が Charlie (u003) に「いいね」 ---")
    engine.perform_like(liker_user_id="u001", liked_content_creator_id="u003")

    # イベント3: Bob (u002) が Alice (u001) のコンテンツに「いいね」
    print("\n--- イベント3: Bob (u002) が Alice (u001) に「いいね」 ---")
    engine.perform_like(liker_user_id="u002", liked_content_creator_id="u001")

    # イベント4: 自然回収の実行
    print("\n--- イベント4: 自然回収の実行 ---")
    engine.perform_natural_recovery()

    # イベント5: Charlie (u003) が Alice (u001) に「いいね」を2回（予算が許す限り）
    print("\n--- イベント5: Charlie (u003) が Alice (u001) に「いいね」 (1回目) ---")
    engine.perform_like(liker_user_id="u003", liked_content_creator_id="u001")
    print("\n--- イベント5: Charlie (u003) が Alice (u001) に「いいね」 (2回目) ---")
    engine.perform_like(liker_user_id="u003", liked_content_creator_id="u001")

    # --- 拡張性のデモンストレーション（ユーザー数を増やした場合） ---
    print("\n\n=== 拡張性テスト: ユーザー数を増やして初期化 ===")
    users_large_test = [
        # 5ユーザーでテスト
        PicsyUser(user_id=f"user{i:03d}", username=f"TestUser{i:03d}") for i in range(5)
    ]
    engine_large = PicsyEngine(
        user_list=users_large_test,
        alpha_like=ALPHA_LIKE,
        gamma_rate=GAMMA_RATE,
        max_iterations=50,  # 反復回数を少し減らしてテスト
        tolerance=1e-6
    )
    # 簡単な操作を実行
    engine_large.perform_like(liker_user_id="user000",
                              liked_content_creator_id="user001")
    engine_large.perform_like(liker_user_id="user000",
                              liked_content_creator_id="user002")
    engine_large.perform_natural_recovery()

    print("\n=== シミュレーション終了 ===")
