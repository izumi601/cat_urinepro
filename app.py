from flask import Flask, render_template, request, jsonify, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os
import numpy as np # <-- 追加: 異常検知ロジックで利用するため

from analysis import process_image, validate_image

# ----------------------------------------------------
# 1. データベースのセットアップ (SQLiteを使用)
# ----------------------------------------------------
DB_PATH = 'sqlite:///database.db'
engine = create_engine(DB_PATH, connect_args={'check_same_thread': False}) 

Base = declarative_base()
Session = sessionmaker(bind=engine)

# ----------------------------------------------------
# 2. クリーニング除外対象IDの定義 (フロントの説明と一致させる)
# ----------------------------------------------------
EXCLUDED_IDS = ['IMG_4930', 'IMG_5047', 'IMG_5025']

# データベースのテーブル定義 (is_abnormalとabnormality_reasonを追加)
class UrineData(Base):
    __tablename__ = 'urine_data'
    id = Column(Integer, primary_key=True)
    day_id = Column(String, unique=True)
    area_mm2 = Column(Float)
    avg_l_value = Column(Float)
    std_l_value = Column(Float)
    is_abnormal = Column(Integer, default=0)         # <--- 追加: 0=正常, 1=異常
    abnormality_reason = Column(String, default="")  # <--- 追加: 異常理由

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
    
    for filename in sorted(os.listdir(folder_path)):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(folder_path, filename)
            day_id = os.path.splitext(filename)[0]
            
            if session.query(UrineData).filter_by(day_id=day_id).first():
                continue 
            
            # クリーニング対象のIDはロードしない（二重で除外するリスクを避ける）
            if day_id in EXCLUDED_IDS:
                print(f"WARN: ID {day_id} は除外対象のためロードをスキップします。")
                continue

            try:
                analysis_data = process_image(file_path)
                
                # 初期データは全て '正常' フラグ (0) で登録
                new_data = UrineData(
                    day_id=analysis_data['day_id'],
                    area_mm2=analysis_data['area_mm2'],
                    avg_l_value=analysis_data['avg_l_value'],
                    std_l_value=analysis_data['std_l_value'],
                    is_abnormal=0, 
                    abnormality_reason="初期データ"
                )
                session.add(new_data)
                count += 1
            except Exception as e:
                print(f"エラー: {filename} の解析に失敗しました: {str(e)}")
                session.rollback()

    session.commit()
    session.close()
    print(f"--- DBに {count} 件の新規初期データをロードしました（{len(EXCLUDED_IDS)}件は除外）。---")

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
        # 【修正点】EXCLUDED_IDS に含まれないデータのみを取得
        # これにより、グラフには18件のクリーンなデータだけが表示される
        data_query = session.query(UrineData).filter(
            ~UrineData.day_id.in_(EXCLUDED_IDS)
        ).all()

        results = [
            {
                'day_id': d.day_id,
                'area_mm2': d.area_mm2,
                'avg_l_value': d.avg_l_value,
                'std_l_value': d.std_l_value,
                'is_abnormal': d.is_abnormal,           # <--- 追加
                'abnormality_reason': d.abnormality_reason # <--- 追加
            } for d in data_query
        ]
        
        return jsonify(results) 
        
    except Exception as e:
        print(f"APIデータ取得エラー: {e}")
        return jsonify({'error': 'データ取得中に内部エラーが発生しました。'}), 500
    finally:
        session.close()

# app.py の upload_file 関数
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'ファイルが選択されていません'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'ファイル名がありません'}), 400
    
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # 1. 画像解析を実行
        try:
            analysis_data = process_image(file_path)
            
            # 解析失敗時 (コイン未検出など) はここでリターン
            if analysis_data['success'] is False:
                return jsonify({'error': f'画像解析エラー: {analysis_data["error"]}'}), 500
                
        except Exception as e:
            return jsonify({'error': f'画像解析エラー: {str(e)}'}), 500
        
        session = Session()
        try:
            # 2. 異常検知のベースラインデータをDBから取得
            # 【重要】異常検知のベースラインは、クリーニング済みのデータ（EXCLUDED_IDSではないもの）を使う
            past_data = session.query(UrineData).filter(
                ~UrineData.day_id.in_(EXCLUDED_IDS)
            ).all()

            
            # --- 【ここに追加】データ信頼性フィルタリングロジック ---
            # 排尿量が過去平均の10%未満であれば、解析失敗と見なす
            if len(past_data) > 5:
                area_values = np.array([d.area_mm2 for d in past_data if d.area_mm2 is not None])
                if area_values.size > 0:
                    area_mean = np.mean(area_values)
                    current_area = analysis_data['area_mm2']
                    MIN_ACCEPTABLE_AREA = area_mean * 0.1
                    
                    if current_area < MIN_ACCEPTABLE_AREA:
                        session.close() 
                        return jsonify({
                            'success': False,
                            'error': f'解析結果が過去平均({area_mean:.0f}mm²)に対して極端に小さく({current_area:.0f}mm²)、画像認識エラーの可能性が高いです。再撮影または別の画像をお試しください。'
                        })
            # --- フィルタリングロジックここまで ---

            
            is_abnormal_flag = 0
            abnormal_message = "【✅ 正常】過去データと比較し、異常はありませんでした。"
            abnormal_reasons = []

            # 3. 異常検知ロジック (10件以上で実行)
            if len(past_data) >= 10:
                area_values = np.array([d.area_mm2 for d in past_data if d.area_mm2 is not None])
                l_values = np.array([d.avg_l_value for d in past_data if d.avg_l_value is not None])
                
                # Zスコア法 (平均 ± 2SD) を再計算
                area_mean, area_std = np.mean(area_values), np.std(area_values)
                l_value_mean, l_value_std = np.mean(l_values), np.std(l_values)
                current_area, current_l_value = analysis_data['area_mm2'], analysis_data['avg_l_value']
                
                if (current_area < area_mean - 2 * area_std) or (current_area > area_mean + 2 * area_std):
                    abnormal_reasons.append("排尿量")
                    
                if (current_l_value < l_value_mean - 2 * l_value_std) or (current_l_value > l_value_mean + 2 * l_value_std):
                    abnormal_reasons.append("濃淡 (L値)")
                
                if abnormal_reasons:
                    is_abnormal_flag = 1
                    abnormal_message = f"【⚠️ 異常検知】{', '.join(abnormal_reasons)} が基準外です。"

            else:
                abnormal_message = "データが少ないため異常判定をスキップしました。"

            # 4. 結果をデータベースに保存
            new_data = UrineData(
                day_id=analysis_data['day_id'],
                area_mm2=analysis_data['area_mm2'],
                avg_l_value=analysis_data['avg_l_value'],
                std_l_value=analysis_data['std_l_value'],
                is_abnormal=is_abnormal_flag, # <--- 追加
                abnormality_reason=abnormal_message # <--- 追加
            )
            session.add(new_data)
            session.commit()
            
            print(f"\n--- 異常検知結果 ---")
            print(f"新規データID: {analysis_data['day_id']}")
            print(abnormal_message)
            print("---------------------\n")
            
            return jsonify({'success': True, 'abnormal_message': abnormal_message})

        except Exception as e:
            session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                return jsonify({'error': f'DB保存エラー: {analysis_data["day_id"]}は既に存在します'}), 500
            # is_abnormalやabnormality_reasonのエラーが出た場合もこれで捕捉できる
            return jsonify({'error': f'DB保存エラー: {str(e)}'}), 500
        finally:
            session.close()


# ----------------------------------------------------
# 6. サーバー起動ブロック
# ----------------------------------------------------

if __name__ == '__main__':
    # 1. データベースを初期化
    init_db()
    
    # 2. 初期データをロード（ここでは除外対象の3件はロードされない）
    load_initial_data(folder_path='initial_images') 
    
    # 3. 開発モードで実行
    app.run(debug=True)