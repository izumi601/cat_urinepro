# 🐱 猫の健康モニタリングダッシュボード

<img width="1439" height="960" alt="スクリーンショット 2025-11-17 3 43 09" src="https://github.com/user-attachments/assets/82fdeb30-88d8-428a-8c1b-fd585327c6c6" />


Python + OpenCV による猫のおしっこ画像解析システム

## 📋 プロジェクト概要

このプロジェクトは、猫のおしっこを撮影した画像を解析し、健康状態をモニタリングするWebアプリケーションです。
100円玉をスケール基準として使用することで、正確な排尿量（mm²）を測定できます。

私の愛猫が尿結石を患っており、日頃から尿の回数などは気にかけています。
「尿の状態を日々観測できたらいいな」
という思いからこのアプリを作りました。

AIや画像処理は、単なる効率化ではなく、
大切な存在の命を守るための技術にもなる。
その可能性を実感したプロジェクトです。

## 🎯 主な機能
✔ 尿画像の色解析（OpenCV）

RGB 値や HSV 色空間を用いて 尿の色味を数値で分析します。

✔ 尿量の相対測定

画像内に置いた「100円玉」を基準にスケールを推定し、尿量の大小を把握します。

✔ 異常判定（簡易アルゴリズム）

健康時の平均値との乖離から、以下の傾向を検出します：

色が濃すぎる → 脱水の可能性

極端な薄さ → 腎臓機能低下の可能性又は水分摂取過多？
（※獣医診断ではありません）

✔ 履歴の保存・可視化

SQLite に日次データを保存し、Streamlit ダッシュボードで履歴をグラフ表示できます。

## 🛠️ 技術スタック

### バックエンド
- **Python 3.8+**
- **Flask**: Webフレームワーク
- **OpenCV**: 画像処理ライブラリ
- **NumPy**: 数値計算

### フロントエンド
- **HTML/CSS/JavaScript**
- **Chart.js**: グラフ描画ライブラリ

### 定点観測の重要性
完璧な測定ではなく、同じ条件での継続的な測定により、**その猫自身のベースラインからの変化**を検出することが目的。


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
cat_urinepro/
├── app.py
├── analysis.py
├── data/
│   ├── raw_data.csv      
│   └── cleaned_data.csv  
├── README.md             
└── initial_images/
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


### 収集データ
- 期間: 2025/09/06 - 09/27（21日間）
- 総データ数: 21件

### データクリーニング
画像の目視確認により、以下3件を測定エラーとして除外：

1. **IMG_4930**: 視覚的にはシミ範囲が広いが、数値は中程度。照明過多によりエッジ検出失敗
2. **IMG_5047**: 視覚的には普通の範囲だが、数値が最大値。背景の白い部分を黄色として誤検出
3. **IMG_5025**: 濃淡が極端に低いが、視覚的にはそこまで濃くない。測定エラーの可能性

最終分析データ: **18件**

### 統計サマリー（クリーニング後）
- 排尿量の中央値: 約24,000 mm²
- 濃淡（L値）の中央値: 約172
- 変動係数（CV）: 約70%（測定誤差が大きい）

### 分析の限界
- **測定誤差**: 照明条件で±30%程度のブレあり
- **目視検証**: 主観的判断（再現性に限界）
- **健康指標**: 排尿量と色のみ。成分分析は不可

短期間のモニタリングではありますが、平均排尿量のベースラインと標準偏差を把握できました。
特に排尿量に大きな変動が見られましたが、Zスコア法（μ±2σ）を使って、排尿量や濃淡における異常値を検出していますが、
まだデータが少なく、信頼性には限界があります。
猫個体の健康状態の把握のためには引き続きデータを蓄積することで、より堅牢なベースラインを構築が必要だと思われる。
特に、排尿量が極端に少ない日や、平均L値（濃淡）が急激に濃くなる日を重点的に監視が必要。


**→ あくまで補助的なモニタリングツールです。異常の疑いがあれば獣医師の診察が必要。**


## 📝 ライセンス

MIT License

## 👤 作成者

あなたの名前
- GitHub:(https://github.com/izumi601/cat_urinepro/tree/main)

## 🙏 謝辞

このプロジェクトは、猫の健康管理をサポートするために作成されました。
OpenCVコミュニティとFlaskコミュニティに感謝します。
