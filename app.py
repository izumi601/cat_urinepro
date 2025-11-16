from flask import Flask, render_template, request, jsonify, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import numpy as np 
from datetime import datetime, timedelta # datetime, timedelta を利用
from analysis import process_image, validate_image
import analysis

# ----------------------------------------------------
# 1. データベースのセットアップ (SQLiteを使用)
# ----------------------------------------------------
DB_PATH = 'sqlite:///database.db'
engine = create_engine(DB_PATH, connect_args={'check_same_thread': False}) 

Base = declarative_base()
Session = sessionmaker(bind=engine)

# ----------------------------------------------------
# 2. クリーニング除外対象IDと日付設定
# ----------------------------------------------------
EXCLUDED_IDS = ['IMG_4930', 'IMG_5047', 'IMG_5025']
START_DATE = datetime(2025, 9, 6)
TOTAL_DAYS = 21 # 全期間21日

# 【重要】画像IDとDay IDの対応表（仮の例）
# 実際には、画像ファイル名と計測日の対応を正確に確認してください
ID_TO_DAY_MAP = {
    'IMG_4930': 1,  # Day 1: 除外
    'IMG_4932': 2,
    'IMG_4940': 3,
    'IMG_4955': 4,
    'IMG_4962': 5,
    'IMG_4964': 6,
    'IMG_4983': 7,
    'IMG_4988': 8,
    'IMG_4993': 9,
    'IMG_4999': 10,
    'IMG_5001': 11,
    'IMG_5002': 12,
    'IMG_5006': 13,
    'IMG_5007': 14,
    'IMG_5013': 15,
    'IMG_5015': 16,
    'IMG_5025': 17, # Day 17: 除外 (以前はDay 21扱いだったが、JSON順序からDay 17に変更)
    'IMG_5035': 18,
    'IMG_5042': 19,
    'IMG_5047': 20, # Day 20: 除外
    'IMG_5050': 21,
    # 実際にはIMG_XXXXとDay番号の対応を正確に定義する
}


# データベースのテーブル定義
class UrineData(Base):
    __tablename__ = 'urine_data'
    id = Column(Integer, primary_key=True)
    day_id = Column(String, unique=True)
    area_mm2 = Column(Float)
    avg_l_value = Column(Float)
    std_l_value = Column(Float)
    is_abnormal = Column(Integer, default=0)
    abnormality_reason = Column(String, default="")
    # グラフのずれを防ぐために、日付情報もDBに持たせる
    day_number = Column(Integer, default=0)       # <--- 追加: Day 1, Day 2, ...
    measurement_date = Column(String, default="") # <--- 追加: 2025-09-06 形式

# 2. テーブルの作成
def init_db():
    Base.metadata.create_all(engine)

# ----------------------------------------------------
# 3. Flaskアプリの初期化
# ----------------------------------------------------
app = Flask(__name__)

# 画像アップロードの保存先を設定
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------------------------------------------
# 4. load_initial_data 関数の定義
# ----------------------------------------------------
def load_initial_data(folder_path='initial_images'):
    """指定されたフォルダ内の画像を全て解析し、DBに保存する"""
    if not os.path.exists(folder_path):
        print(f"初期データフォルダ '{folder_path}' が見つかりません。スキップします。")
        return

    session = Session()
    count = 0
    
    # 画像ファイル名を昇順にソートして、Day IDに対応付ける
    sorted_filenames = sorted(os.listdir(folder_path))
    
    # JSONの順序と Day ID の対応を作成
    # JSONの順番は Day 1, Day 2, ... に対応していると仮定
    file_to_day_map = {}
    day_counter = 1
    for i, filename in enumerate(sorted_filenames):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            day_id = os.path.splitext(filename)[0]
            # 既に Day ID と Day Number の対応がID_TO_DAY_MAPで定義されているはず
            day_number = ID_TO_DAY_MAP.get(day_id, i + 1)
            file_to_day_map[day_id] = day_number
            
            # DBにDay IDが存在するかチェック
            if session.query(UrineData).filter_by(day_id=day_id).first():
                continue 
            
            # クリーニング対象のIDはロードしない
            if day_id in EXCLUDED_IDS:
                print(f"WARN: ID {day_id} (Day {day_number}) は除外対象のためロードをスキップします。")
                # 除外データもDBに登録するが、解析結果はNoneにし、is_abnormal=2（除外）としてマークする
                measurement_date = (START_DATE + timedelta(days=day_number - 1)).strftime('%Y-%m-%d')
                new_data = UrineData(
                    day_id=day_id,
                    area_mm2=None,  # Noneを登録
                    avg_l_value=None, # Noneを登録
                    std_l_value=None, # Noneを登録
                    is_abnormal=2, # 2=除外 (グラフ表示用)
                    abnormality_reason="クリーニング除外データ",
                    day_number=day_number,
                    measurement_date=measurement_date
                )
                session.add(new_data)
                count += 1
                continue # 次のファイルへ

            # 正常なデータを解析
            try:
                file_path = os.path.join(folder_path, filename)
                analysis_data = process_image(file_path)
                measurement_date = (START_DATE + timedelta(days=day_number - 1)).strftime('%Y-%m-%d')
                
                # 正常データは '正常' フラグ (0) で登録
                new_data = UrineData(
                    day_id=analysis_data['day_id'],
                    area_mm2=analysis_data['area_mm2'],
                    avg_l_value=analysis_data['avg_l_value'],
                    std_l_value=analysis_data['std_l_value'],
                    is_abnormal=0, 
                    abnormality_reason="初期データ",
                    day_number=day_number,              # <--- 追加
                    measurement_date=measurement_date # <--- 追加
                )
                session.add(new_data)
                count += 1
            except Exception as e:
                print(f"エラー: {filename} の解析に失敗しました: {str(e)}")
                session.rollback()

    session.commit()
    session.close()
    print(f"--- DBに {count} 件の新規データをロードしました（内3件は除外マーク）。---")

# ----------------------------------------------------
# 5. エンドポイントの定義
# ----------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    session = Session()
    try:
        # 【修正点】全データを Day Number 順に取得
        # Day Number は 1 から 21 まで連番になっている（None値含む）
        data_query = session.query(UrineData).order_by(UrineData.day_number).all()

        results = []
        for d in data_query:
            results.append({
                'day_label': f"Day {d.day_number}", # グラフラベルとして使用
                'measurement_date': d.measurement_date, # X軸データとして使用
                'day_id': d.day_id,
                # None値を返すことでグラフの線が途切れる
                'area_mm2': d.area_mm2,
                'avg_l_value': d.avg_l_value,
                'std_l_value': d.std_l_value,
                'is_abnormal': d.is_abnormal,
                'abnormality_reason': d.abnormality_reason,
                'is_excluded': (d.is_abnormal == 2) # 除外マークが付いているか
            })
        
        # グラフは21件のデータ（欠損値含む）を受け取り、日付軸で表示する
        return jsonify(results) 

    except Exception as e:
        print(f"APIデータ取得エラー: {e}")
        return jsonify({'error': 'データ取得中に内部エラーが発生しました。'}), 500
    finally:
        session.close()

# ... (upload_file 関数は変更なし) ...

# ----------------------------------------------------
# 6. サーバー起動ブロック
# ----------------------------------------------------

if __name__ == '__main__':
    # 1. データベースを初期化
    init_db()
    
    # 2. 初期データをロード（ここでは除外対象の3件はNone値で登録される）
    load_initial_data(folder_path='initial_images') 
    
    # 3. 開発モードで実行
    app.run(debug=True)