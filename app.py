from flask import Flask, render_template, request, jsonify, redirect, url_for
from sqlalchemy import create_engine, Column, Integer, Float, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

from analysis import process_image 

# ----------------------------------------------------
# 1. データベースのセットアップ (SQLiteを使用)
# ----------------------------------------------------
DB_PATH = 'sqlite:///database.db'
engine = create_engine(DB_PATH, connect_args={'check_same_thread': False}) 

Base = declarative_base()
Session = sessionmaker(bind=engine)

# データベースのテーブル定義
class UrineData(Base):
    __tablename__ = 'urine_data'
    id = Column(Integer, primary_key=True)
    day_id = Column(String, unique=True)
    area_mm2 = Column(Float)
    avg_l_value = Column(Float)
    std_l_value = Column(Float)

# 2. テーブルの作成
def init_db():
    Base.metadata.create_all(engine)

# ----------------------------------------------------
# 3. Flaskアプリの初期化をここ（上部）に移動
# ----------------------------------------------------
app = Flask(__name__)

# 画像アップロードの保存先を設定
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ----------------------------------------------------
# 4. load_initial_data 関数の定義をここに移動
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

            try:
                analysis_data = process_image(file_path)
                
                new_data = UrineData(
                    day_id=analysis_data['day_id'],
                    area_mm2=analysis_data['area_mm2'],
                    avg_l_value=analysis_data['avg_l_value'],
                    std_l_value=analysis_data['std_l_value']
                )
                session.add(new_data)
                count += 1
            except Exception as e:
                print(f"エラー: {filename} の解析に失敗しました: {str(e)}")
                session.rollback()

    session.commit()
    session.close()
    print(f"--- DBに {count} 件の新規初期データをロードしました。---")

# ----------------------------------------------------
# 5. エンドポイントの定義 (ここから @app.route を使う)
# ----------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data', methods=['GET'])
def get_data():
    """データベースから全データを取得し、JSONで返すAPIエンドポイント"""
    session = Session()
    try:
        # データベースから全てのデータを取得
        data = session.query(UrineData).all()

        # データをJSON形式に変換し、results に代入
        results = [
            {
                'day_id': d.day_id,
                # Pythonのfloat(NaNなど)がJSONでエラーにならないよう処理
                'area_mm2': d.area_mm2, 
                'avg_l_value': d.avg_l_value,
                'std_l_value': d.std_l_value
            } for d in data
        ]
        return jsonify(results)
        
    except Exception as e:
        print(f"APIデータ取得エラー: {e}")
        return jsonify({'error': 'データ取得中に内部エラーが発生しました。'}), 500
    finally:
        session.close()

@app.route('/upload', methods=['POST'])
def upload_file():
    # ... (省略) ...
    return redirect(url_for('index'))


# ----------------------------------------------------
# 6. サーバー起動ブロック（呼び出しはここ）
# ----------------------------------------------------

if __name__ == '__main__':
    # 1. アプリ起動時にデータベースを初期化（新しい database.db が作成される）
    init_db()
    
    # 2. 21枚の初期データを一括でロードする
    load_initial_data(folder_path='initial_images') 
    
    # 3. 開発モードで実行
    app.run(debug=True)