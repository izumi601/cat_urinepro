import pandas as pd
import json
from datetime import datetime, timedelta
import os

# ファイルパスの定義
# data/data.json を参照するように修正
JSON_PATH = os.path.join('data', 'data.json')
RAW_CSV_PATH = os.path.join('data', 'raw_data.csv')
CLEANED_CSV_PATH = os.path.join('data', 'cleaned_data.csv')

# data.jsonを読み込み
try:
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
except FileNotFoundError:
    print(f"エラー: JSONファイルが見つかりません。{JSON_PATH} が存在するか確認してください。")
    exit()
except json.JSONDecodeError:
    print("エラー: data/data.json の形式が正しくありません。中身がJSON配列か確認してください。")
    exit()


df = pd.DataFrame(data)

# --- 特徴量エンジニアリングとデータ補完 ---

# 1. タイムスタンプの追加
# (Day 1から開始するため、len(df)に依存して日付を生成)
start_date = datetime(2025, 9, 6)
df['timestamp'] = [start_date + timedelta(days=i) for i in range(len(df))]

# 2. 画像ファイル名の追加（初期データの形式に合わせて拡張子を修正）
# 初期データは通常 day1.png, day2.png の形式
df['image_filename'] = df['day_id'] + '.png'


# raw_data.csv（全データ）の書き出し
os.makedirs('data', exist_ok=True)
df.to_csv(RAW_CSV_PATH, index=False)

# --- データクレンジング（既知のエラーの除外） ---

# 画像検証済みの測定エラーを除外

# known_errors_original = ['IMG_4930', 'IMG_5047', 'IMG_5025']
known_errors = ['IMG_4930', 'IMG_5047', 'IMG_5025']
# 実際のデータに合わせて、除外したい day_id をリストに入れてください。

cleaned_df = df[~df['day_id'].isin(known_errors)]

# cleaned_data.csv の書き出し
cleaned_df.to_csv(CLEANED_CSV_PATH, index=False)

print("--- データセット生成完了 ---")
print(f"✓ {RAW_CSV_PATH} (全データ): {len(df)}件")
print(f"✓ {CLEANED_CSV_PATH} (クレンジング済): {len(cleaned_df)}件（{len(df) - len(cleaned_df)}件除外）")