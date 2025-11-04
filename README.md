# 🐱 猫の健康モニタリングダッシュボード

Python + OpenCV による猫のおしっこ画像解析システム

## 📋 プロジェクト概要

このプロジェクトは、猫のおしっこを撮影した画像を解析し、健康状態をモニタリングするWebアプリケーションです。
100円玉をスケール基準として使用することで、正確な排尿量（mm²）を測定できます。

## 🎯 主な機能

- **画像解析**: OpenCVを使用した高精度な画像処理
  - HSVカラースペースでの黄色領域抽出
  - Hough変換による100円玉の自動検出
  - Lab色空間を使った濃淡の定量化

- **データの可視化**:
  - 排尿量の推移グラフ
  - 濃淡（L値）の推移グラフ
  - 色の均一性（標準偏差）の推移グラフ

- **データ管理**:
  - JSON形式でのデータ永続化
  - 統計情報の自動計算
  - データの一括削除機能

## 🛠️ 技術スタック

### バックエンド
- **Python 3.8+**
- **Flask**: Webフレームワーク
- **OpenCV**: 画像処理ライブラリ
- **NumPy**: 数値計算

### フロントエンド
- **HTML/CSS/JavaScript**
- **Chart.js**: グラフ描画ライブラリ

## 📦 インストール方法

### 1. リポジトリのクローン
```bash
git clone https://github.com/yourusername/cat-urine-monitor.git
cd cat-urine-monitor
```

### 2. 仮想環境の作成（推奨）
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 依存関係のインストール
```bash
pip install -r requirements.txt
```

### 4. フォルダ構成の確認
```
cat-urinepro/
├── app.py                 # Flaskアプリケーション
├── analysis.py            # 画像解析モジュール
├── requirements.txt       # 依存関係
├── templates/
│   └── index.html        # フロントエンド
```

## 🚀 使い方

### サーバーの起動
```bash
python app.py
```

ブラウザで `http://localhost:5000` にアクセス

### 画像のアップロード
1. 100円玉と一緒に撮影したおしっこの画像を準備
2. 「ファイルを選択」ボタンから画像を選択
3. 「解析して追加」ボタンをクリック
4. 解析結果がグラフに自動追加されます

## 📊 解析項目

| 項目 | 説明 | 単位 |
|------|------|------|
| 排尿量 | 100円玉を基準にした物理的な面積 | mm² |
| 濃淡（平均L値） | Lab色空間のL値の平均（高いほど薄い） | 0-255 |
| 濃淡の安定性 | L値の標準偏差（低いほど均一） | 数値 |

## 🎨 画像解析アルゴリズム

### 1. 黄色領域の抽出
```python
# HSVカラースペースに変換
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# 黄色の範囲でマスク作成
lower_bound = np.array([20, 50, 50])
upper_bound = np.array([40, 255, 255])
mask = cv2.inRange(hsv, lower_bound, upper_bound)
```

### 2. スケール計算（100円玉検出）
```python
# Hough変換で円を検出
circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, ...)

# ピクセル/mmの換算率を計算
px_per_mm = circle_radius / (coin_diameter_mm / 2)
```

### 3. 濃淡の定量化
```python
# Lab色空間に変換してL値を取得
lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
l_channel = lab[:, :, 0]

# シミ部分のL値を抽出して統計計算
avg_l_value = np.mean(l_values_in_urine)
std_l_value = np.std(l_values_in_urine)
```

```

## 🌐 デプロイ方法

### Render でのデプロイ（推奨・無料）

1. [Render](https://render.com/) にサインアップ
2. 「New Web Service」を作成
3. GitHubリポジトリを接続
4. 設定：
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. `requirements.txt` に `gunicorn` を追加

### Railway でのデプロイ

1. [Railway](https://railway.app/) にサインアップ
2. 「New Project」→「Deploy from GitHub repo」
3. リポジトリを選択して自動デプロイ

## 🔬 今後の拡張案

- [ ] 機械学習モデルによる異常検知
- [ ] 日付指定機能
- [ ] PDFレポート出力
- [ ] 複数の猫の管理機能
- [ ] スマートフォンアプリ対応

## 📝 ライセンス

MIT License

## 👤 作成者

あなたの名前
- GitHub: [@izumi601](https://github.com/yourusername)

## 🙏 謝辞

このプロジェクトは、猫の健康管理をサポートするために作成されました。
OpenCVコミュニティとFlaskコミュニティに感謝します。
