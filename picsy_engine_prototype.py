# core_logic_prototype.py

import numpy as np  # NumPyライブラリを 'np' という名前でインポート

# --- システムの基本設定 (プロトタイプ用) ---
NUM_USERS = 3  # システムに参加する総ユーザー数
USER_NAMES = ["Alice", "Bob", "Charlie"]  # 各ユーザーの名前 (表示用)

# プログラム開始のメッセージ
print("--- PICSY-TrustLike コアロジック プロトタイプ ---")
print(f"設定ユーザー数: {NUM_USERS}人 ({', '.join(USER_NAMES)})")
print("-" * 40)  # 区切り線

# --- 1. 初期評価行列 E の定義 ---
print("\n[ステップ1: 初期評価行列 E の定義]")

# 各行はユーザーiから他のユーザーjへの評価E_ij (予算E_iiを含む)
# 行インデックス: 0:Alice, 1:Bob, 2:Charlie
# 列インデックス: 0:Alice, 1:Bob, 2:Charlie
initial_E_data = [
    [0.2000, 0.3333, 0.4667],  # Aliceの評価 (Alice予算, Alice→Bob, Alice→Charlie)
    [0.2182, 0.2000, 0.5818],  # Bobの評価   (Bob→Alice, Bob予算, Bob→Charlie)
    # Charlieの評価(Charlie→Alice, Charlie→Bob, Charlie予算)
    [0.0571, 0.7429, 0.2000]
]

# PythonリストをNumPy配列に変換
E = np.array(initial_E_data, dtype=float)  # データ型を浮動小数点数に指定

print("初期評価行列 E:")
print(E)
print(f"行列の形状 (ユーザー数 x ユーザー数): {E.shape}")
# 各行の和を計算 (axis=1 は行ごとの合計を指定)
row_sums_E = np.sum(E, axis=1)
print(f"E の各行の和: {row_sums_E}")

# 全ての行和が1に近いかを確認 (浮動小数点数のため厳密な比較は避ける)
# np.allclose(a, b, rtol, atol) は a と b の要素が相対誤差rtolと絶対誤差atolの範囲で近いか判定
if np.allclose(row_sums_E, 1.0, rtol=1e-5, atol=1e-8):
    print("検証OK: E の全ての行の和はほぼ1です。")
else:
    print("警告: E の行の和が1になっていない行があります！データや計算を確認してください。")
    for i, row_sum in enumerate(row_sums_E):
        if not np.isclose(row_sum, 1.0, rtol=1e-5, atol=1e-8):
            print(
                f"  - {USER_NAMES[i]} の行 (インデックス {i}) の和: {row_sum:.8f} (1との差: {abs(row_sum - 1.0):.2e})")
print("-" * 40)


def calculate_E_prime(E_matrix, num_users):
    """
    評価行列 E から貢献度計算用行列 E' を計算する (仮想中央銀行法)。
    E' = E - B + (B @ D) / (N - 1)

    Args:
        E_matrix (np.ndarray): N x N の評価行列。
        num_users (int): 総ユーザー数 N。

    Returns:
        np.ndarray: N x N の貢献度計算用行列 E'。
    """
    if num_users <= 1:
        # N-1 でのゼロ除算を避けるためのチェック
        raise ValueError("ユーザー数は2以上である必要があります。")

    # 1. 予算行列 B の作成
    #    E_matrix の対角成分 (E_ii) を取り出し、それらを対角に持つ行列 B を作る
    diagonal_elements_E = np.diag(E_matrix)  # E_matrix の対角成分を1次元配列として取得
    B = np.diag(diagonal_elements_E)      # 1次元配列を対角行列に変換 (他の要素は0)

    # 2. 分配行列 D の作成
    #    D は対角成分が0で、非対角成分が1の N x N 行列
    #    np.eye(num_users) は単位行列 (対角成分が1で他が0)
    #    np.ones((num_users, num_users)) は全要素が1の行列
    D = np.ones((num_users, num_users)) - np.eye(num_users)

    # 3. E' の計算 (PICSY資料 式4.62)
    #    B @ D は行列Bと行列Dの積 (Python 3.5+ の行列積演算子)
    #    num_users - 1 で割る
    E_prime_matrix = E_matrix - B + (B @ D) / (num_users - 1)

    return E_prime_matrix


# --- 2. E から E' への変換 ---
print("\n[ステップ2: E から E' への変換 (仮想中央銀行法)]")

try:
    E_prime0 = calculate_E_prime(E, NUM_USERS)  # E0 を E に修正 (上で定義した変数名)
    print("貢献度計算用行列 E'^(0):")
    print(E_prime0)

    # E' の検証
    print(f"E'^(0) の形状: {E_prime0.shape}")
    diagonal_E_prime0 = np.diag(E_prime0)  # E_prime0の対角成分を取得
    print(f"E'^(0) の対角成分 (ほぼ0のはず): {diagonal_E_prime0}")
    row_sums_E_prime0 = np.sum(E_prime0, axis=1)
    print(f"E'^(0) の各行の和 (ほぼ1のはず): {row_sums_E_prime0}")

    # 前回のシミュレーション結果 E'^(0) (検証用)
    expected_E_prime0_data = np.array([
        [0.0000, 0.4333, 0.5667],
        [0.3182, 0.0000, 0.6818],
        [0.1571, 0.8429, 0.0000]
    ])

    # 検証
    valid_E_prime = True
    if not np.allclose(E_prime0, expected_E_prime0_data, atol=1e-4):  # 許容誤差を少し設定
        print("警告: E'^(0) が期待値と異なります。")
        print("  期待値:")
        print(expected_E_prime0_data)
        valid_E_prime = False
    if not np.allclose(diagonal_E_prime0, 0.0, atol=1e-8):
        print(f"警告: E'^(0) の対角成分が厳密に0ではありません: {diagonal_E_prime0}")
        # 実質的に0に近いか確認するために表示
        valid_E_prime = False
    if not np.allclose(row_sums_E_prime0, 1.0, rtol=1e-5, atol=1e-8):
        print(f"警告: E'^(0) の行和が1になっていません: {row_sums_E_prime0}")
        valid_E_prime = False

    if valid_E_prime:
        print("検証OK: E'^(0) は期待値と一致し、対角成分はほぼ0、行和はほぼ1です。")

except ValueError as e:
    print(f"エラー: E' の計算中に問題が発生しました - {e}")

print("-" * 40)
