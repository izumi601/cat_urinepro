import cv2
import numpy as np
import os
import pandas as pd
from datetime import datetime, timedelta

# 100円玉の直径（mm）
COIN_DIAMETER_MM = 22.6

# ==========================================
# 1. 画像解析の処理 (process_image)
# ==========================================
def process_image(image_path):
    """
    画像パスを受け取り、尿の解析結果を返します。
    """
    try:
        # print(f"--- INFO: Analysing image: {image_path} ---") # Renderのログを減らすためコメントアウト
        
        # 画像の読み込み
        img = cv2.imread(image_path)
        
        if img is None:
            return {
                'success': False,
                'error': '画像の読み込みに失敗しました'
            }

        # --- 尿の領域検出 ---
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([20, 50, 50]) # 黄色の下限
        upper_bound = np.array([40, 255, 255]) # 黄色の上限
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        area_pixel = np.sum(mask > 0) # シミ領域のピクセル数

        # --- スケール換算（コイン検出） ---
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
            circle_radius = circles[0][0][2]
            px_per_mm = circle_radius / (COIN_DIAMETER_MM / 2)

            if px_per_mm > 0:
                area_mm2 = area_pixel / (px_per_mm ** 2)

        # --- 濃淡の定量化（L値） ---
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        l_values_in_urine = l_channel[mask > 0]

        avg_l_value = None
        std_l_value = None

        if len(l_values_in_urine) > 0:
            avg_l_value = float(np.mean(l_values_in_urine))
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
                'error': '100円玉が検出できませんでした。'
            }

    except Exception as e:
        # print(f"ERROR: {str(e)}") # Renderのログを減らすためコメントアウト
        return {
            'success': False,
            'error': f'解析エラー: {str(e)}'
        }

# ==========================================
# 2. 画像の事前検証関数 (validate_image)
#    - process_images_in_directory より前に定義
# ==========================================
def validate_image(image_path):
    """
    ファイルが画像であり、解析に適しているか検証する。
    """
    # 拡張子チェック
    if not (image_path.lower().endswith('.png') or 
            image_path.lower().endswith('.jpg') or
            image_path.lower().endswith('.jpeg')):
        return False, "非画像ファイルです"

    # ファイルサイズチェック（任意）
    if os.path.getsize(image_path) < 1024: # 1KB未満は小さすぎる
        return False, "ファイルサイズが小さすぎます"
    
    return True, "OK"


# ==========================================
# 3. ディレクトリ内の画像処理（app.pyから呼ばれる）
# ==========================================
def process_images_in_directory(image_dir):
    """
    指定されたディレクトリ内の画像を処理し、成功した結果のリストを返します。
    """
    data = []

    # ディレクトリ内の画像を一つずつ処理
    for image_filename in os.listdir(image_dir):
        image_path = os.path.join(image_dir, image_filename)
        
        # 呼び出しより前に validate_image が定義されているため、NameErrorは出ない
        is_valid, reason = validate_image(image_path) 
        if not is_valid:
            # print(f"SKIP: {image_filename} - {reason}")
            continue

        result = process_image(image_path)

        if result['success']:
            data.append(result)
        # else:
            # print(f"FAIL: {image_filename} - {result['error']}")

    return data


# ==========================================
# 4. ローカルテスト用の実行ブロック (Renderデプロイでは実行されない)
# ==========================================
if __name__ == '__main__':
    # 注意: このブロックはローカルテスト専用です。
    # Renderで実行されるのは app.py の初期化ロジックです。
    print("--- Analysis Script Local Test Start ---")
    
    image_directory = 'initial_images'
    if not os.path.exists(image_directory):
        print(f"WARN: 初期画像フォルダ '{image_directory}' が見つかりません。")
        
    initial_results = process_images_in_directory(image_directory)
    print(f"分析完了。成功したレコード数: {len(initial_results)}")
    
    if initial_results:
        df = pd.DataFrame(initial_results)
        # ローカルでの動作確認用に出力
        # df.to_csv('local_test_results.csv', index=False)
        print("ローカルテスト結果のデータ構造確認済み。")
    print("--- Analysis Script Local Test End ---")