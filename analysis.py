import cv2
import numpy as np
import os
import pandas as pd
from datetime import datetime, timedelta

# 100円玉の直径（mm）
COIN_DIAMETER_MM = 22.6

# ==========================================
# 画像解析の処理
# ==========================================
def process_image(image_path):
    """
    画像パスを受け取り、尿の解析結果を返します。
    
    Args:
        image_path (str): 解析する画像のパス
    
    Returns:
        dict: 解析結果 {
            'day_id': str,
            'area_mm2': float,
            'avg_l_value': float,
            'std_l_value': float,
            'success': bool,
            'error': str (optional)
        }
    """
    try:
        print(f"--- INFO: Analysing image: {image_path} ---")
        
        # 画像の読み込み
        img = cv2.imread(image_path)
        
        if img is None:
            return {
                'success': False,
                'error': '画像の読み込みに失敗しました'
            }

        # HSVに変換
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # シミ領域を抽出するための色範囲（黄色）
        lower_bound = np.array([20, 50, 50])
        upper_bound = np.array([40, 255, 255])

        # マスク作成
        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        # 面積を計算（シミ領域のピクセル数）
        area_pixel = np.sum(mask > 0)

        # Hough Circlesでコインの検出とスケール換算
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        circles = cv2.HoughCircles(
            gray, 
            cv2.HOUGH_GRADIENT, 
            dp=1.2, 
            minDist=50,
            param1=120, 
            param2=30, 
            minRadius=20, 
            maxRadius=200
        )
        
        px_per_mm = None
        area_mm2 = None

        if circles is not None:
            circle_radius = circles[0][0][2]  # 半径（px）
            px_per_mm = circle_radius / (COIN_DIAMETER_MM / 2)

            if px_per_mm > 0:
                # 物理的なシミ面積mm²に換算
                area_mm2 = area_pixel / (px_per_mm ** 2)

        # 濃淡の（L値）の定量化（Lab利用）
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]  # L (Lightness/明るさ) チャンネルを取得

        # マスクを使ってシミ部分のL値を抽出
        l_values_in_urine = l_channel[mask > 0]

        avg_l_value = None
        std_l_value = None

        if len(l_values_in_urine) > 0:
            # シミ部分のL値の平均（濃淡）
            avg_l_value = float(np.mean(l_values_in_urine))
            # シミ部分のL値の標準偏差（濃淡の分布の狭さ/安定性）
            std_l_value = float(np.std(l_values_in_urine))

        # ファイル名から day_id を抽出
        file_name = os.path.basename(image_path)
        day_id = os.path.splitext(file_name)[0]

        # 結果を返す
        if area_mm2 is not None and avg_l_value is not None:
            return {
                'success': True,
                'day_id': day_id,
                'area_mm2': round(area_mm2, 2),
                'avg_l_value': round(avg_l_value, 2),
                'std_l_value': round(std_l_value, 2) if std_l_value else 0,
                'area_pixel': int(area_pixel)
            }
        else:
            return {
                'success': False,
                'error': '100円玉が検出できませんでした。画像に100円玉が写っているか確認してください。'
            }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        return {
            'success': False,
            'error': f'解析エラー: {str(e)}'
        }

# ==========================================
# 画像ファイルを処理してCSVに追加
# ==========================================
def process_images_in_directory(image_dir):
    """
    指定されたディレクトリ内の画像を処理し、結果をCSVに保存する
    
    Args:
        image_dir (str): 画像ファイルが格納されているディレクトリパス
    """
    data = []

    # ディレクトリ内の画像を一つずつ処理
    for image_filename in os.listdir(image_dir):
        image_path = os.path.join(image_dir, image_filename)
        
        if not validate_image(image_path)[0]:
            continue

        result = process_image(image_path)

        if result['success']:
            data.append(result)

    # 結果をデータフレームに変換
    df = pd.DataFrame(data)

    # CSVファイルとして保存
    df.to_csv('data/raw_data.csv', index=False)
    print("✓ raw_data.csv を生成しました")

    # 測定エラーを除外したデータ（cleaned_data.csv）
    cleaned_df = df[df['success'] == True].copy()
    cleaned_df.to_csv('data/cleaned_data.csv', index=False)
    print(f"✓ cleaned_data.csv を生成しました（{len(df) - len(cleaned_df)}件除外）")

# 画像ディレクトリの指定
image_directory = 'initial_images/'

# 画像を処理してCSVを生成
process_images_in_directory(image_directory)
