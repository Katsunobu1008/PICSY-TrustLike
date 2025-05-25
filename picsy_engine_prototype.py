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
