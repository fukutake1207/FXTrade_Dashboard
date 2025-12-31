# FX Discretionary Trading Cockpit

USDJPYの裁量トレードを支援する統合ダッシュボードシステム

## プロジェクト概要

FX Discretionary Trading Cockpitは、USDJPY通貨ペアの裁量トレーダー向けに設計された、リアルタイム市場分析とコンテキスト情報を提供するWebダッシュボードです。MT5チャートと連携し、価格分析だけでなく、市場のナラティブ（物語）とコンテキストを提供することで、より質の高いトレード判断を支援します。

### 設計思想

- **MT5カスタムインジケーター**: リアルタイム価格分析（「今、価格がどう動いているか」）
- **Webダッシュボード**: コンテキスト・ナラティブ（「なぜこう動くのか、次に何が起きるか」）

**Single Source of Truth原則**: 価格データの真実はMT5のみが持ち、同じ計算ロジックを2箇所に持たない。

## 主要機能

### 1. 価格データと統計情報
- 週間価格サマリー（週初値、現在値、高値、安値、レンジ）
- 過去4週間の同曜日・同時間帯のボラティリティ統計
- セッション別平均レンジ（東京/ロンドン/NY）

### 2. 相関資産モニタリング
- ゴールド（XAU/USD）、日経225、S&P500との相関分析
- 過去20営業日のローリング相関係数
- 相関に基づく市場動向の洞察

### 3. 市場セッション情報
- 東京市場の詳細モニタリング（優先セッション）
- ロンドン・ニューヨーク市場のナラティブ情報
- セッション進行状況とタイムライン表示

### 4. AIナラティブ生成
- セッション毎（1日3回）のマーケットナラティブ自動生成
- Claude API / Gemini APIによるマクロ環境分析
- 経済指標、ニュース、テクニカル状況の統合サマリー

### 5. シナリオ分析と重要レベル検出
- 重要価格レベルの自動検出（スイングハイロー、ラウンドナンバー、ピボット）
- If-Thenトレーディングシナリオの自動生成
- リスクリワード比の計算

### 6. アラートシステム
- 重要経済指標アラート（30分前通知）
- セッション開始アラート
- ボラティリティ急上昇アラート
- 重要レベル接近アラート

### 7. トレードログとパフォーマンス分析
- トレード履歴の記録とコンテキスト保存
- セッション別パフォーマンス分析
- 改善ポイントの自動抽出

## 技術スタック

### フロントエンド
- **フレームワーク**: React 18 + TypeScript
- **ビルドツール**: Vite 5
- **スタイリング**: Tailwind CSS
- **チャート**: Recharts
- **アイコン**: Lucide React
- **HTTP クライアント**: Axios
- **日時処理**: date-fns

### バックエンド
- **フレームワーク**: Python FastAPI
- **非同期処理**: Uvicorn + asyncio
- **データベース**: SQLAlchemy (async) + SQLite
- **データ分析**: pandas
- **バリデーション**: Pydantic
- **環境変数**: python-dotenv
- **HTTP クライアント**: httpx
- **MT5連携**: MetaTrader5 Python Package (v5.0.5430)
  - **対応Python**: 3.5以上（推奨: 3.10+）
  - **対応OS**: Windows専用（Windows 10/11 64bit）
  - **機能**: リアルタイム価格データ取得、履歴データ取得、ポジション管理
- **マーケットデータ**: yfinance

### AI統合
- **ナラティブ生成**: Claude API (claude-sonnet-4-5) / Google Gemini API

## システム要件

- **Python**: 3.10 以上（推奨: 3.10 / 3.11 / 3.12 / 3.13）
  - MetaTrader5 Pythonパッケージ（最新版: 5.0.5430）は Python 3.5以上をサポートしますが、最新のセキュリティと機能を考慮して3.10以上を推奨
  - **重要**: MetaTrader5パッケージは**Windows専用**です。Mac/Linuxでは動作しません
- **Node.js**: 18.0 以上
- **OS**: Windows 10/11（MT5連携のため必須）
- **MetaTrader 5**: インストール済み（価格データ取得用）
  - 公式サイト: https://www.metatrader5.com/

## プロジェクトステータス

**現在の状態**: 📋 設計・計画フェーズ

このリポジトリは現在、設計書とドキュメントを含む計画段階にあります。実装は別ブランチ（`feature/initial-setup`）で進行中で、レビュー・テスト後にmainブランチにマージされる予定です。

### 現在利用可能なドキュメント

- `docs/金融市場監視システム設計.md` - 詳細な設計仕様書
- `AGENTS.md` - AI エージェント関連のドキュメント
- `GEMINI.md` - Gemini API 統合に関するドキュメント
- `README.md` - このファイル（プロジェクト概要）

## セットアップ（実装完了後）

> **注意**: 以下の手順は実装が`main`ブランチにマージされた後に有効になります。
> 現在実装を試す場合は、`feature/initial-setup`ブランチをチェックアウトしてください。

### 実装ブランチで試す場合

```bash
git clone https://github.com/fukutake1207/FXTrade_Dashboard.git
cd FXTrade_Dashboard
git checkout feature/initial-setup
```

### 1. バックエンドのセットアップ

```bash
cd backend

# 仮想環境の作成
python -m venv .venv

# 仮想環境の有効化（Windows）
.venv\Scripts\activate

# 仮想環境の有効化（Mac/Linux）
source .venv/bin/activate

# 依存関係のインストール
pip install -r requirements.txt

# MT5パッケージの確認（Windows環境のみ）
# requirements.txtに含まれていますが、個別にインストールする場合：
# pip install MetaTrader5

# 環境変数の設定
# .env ファイルを作成し、以下を設定
# ANTHROPIC_API_KEY=your_claude_api_key
# GEMINI_API_KEY=your_gemini_api_key
```

**注意**: MetaTrader5パッケージはWindows専用です。Mac/Linuxでは以下のエラーが発生します：
- `ERROR: Could not find a version that satisfies the requirement MetaTrader5`
- このプロジェクトを非Windows環境で開発する場合は、MT5機能をモックする必要があります

### 2. フロントエンドのセットアップ

```bash
cd frontend

# 依存関係のインストール
npm install
```

### 3. データベースの初期化

```bash
cd backend
python -m src.init_db
```

## 使用方法（実装完了後）

### バックエンドの起動

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

APIドキュメント: http://localhost:8000/docs

### フロントエンドの起動

```bash
cd frontend
npm run dev
```

ダッシュボード: http://localhost:5173

## プロジェクト構造

### 現在の構造（mainブランチ）

```
FXTrade_Dashboard/
├── docs/
│   └── 金融市場監視システム設計.md  # 設計仕様書
├── AGENTS.md                         # AI エージェント関連ドキュメント
├── GEMINI.md                         # Gemini API 統合ドキュメント
└── README.md                         # このファイル
```

### 計画中の構造（実装完了後）

```
FXTrade_Dashboard/
├── backend/                   # バックエンド実装（Python FastAPI）
│   ├── src/
│   │   ├── routers/           # API エンドポイント
│   │   │   ├── alerts.py      # アラート API
│   │   │   ├── correlations.py # 相関分析 API
│   │   │   ├── narratives.py  # ナラティブ API
│   │   │   ├── prices.py      # 価格データ API
│   │   │   ├── scenarios.py   # シナリオ API
│   │   │   ├── sessions.py    # セッション API
│   │   │   └── trades.py      # トレードログ API
│   │   ├── services/          # ビジネスロジック
│   │   │   ├── alert_service.py
│   │   │   ├── claude_service.py
│   │   │   ├── correlation_analyzer.py
│   │   │   ├── data_collector.py
│   │   │   ├── gemini_service.py
│   │   │   ├── market_data_service.py
│   │   │   ├── mt5_service.py
│   │   │   ├── scenario_service.py
│   │   │   ├── session_service.py
│   │   │   └── trade_analysis_service.py
│   │   ├── database.py        # データベース設定
│   │   ├── models.py          # データモデル
│   │   ├── init_db.py         # DB 初期化スクリプト
│   │   └── main.py            # FastAPI アプリケーション
│   ├── requirements.txt       # Python 依存関係
│   └── .env                   # 環境変数（要作成）
├── frontend/                  # フロントエンド実装（React + TypeScript）
│   ├── src/
│   │   ├── components/        # React コンポーネント
│   │   │   ├── AlertPanel.tsx
│   │   │   ├── CorrelationPanel.tsx
│   │   │   ├── NarrativePanel.tsx
│   │   │   ├── PricePanel.tsx
│   │   │   ├── ScenarioPanel.tsx
│   │   │   ├── SessionPanel.tsx
│   │   │   └── TradePanel.tsx
│   │   ├── lib/
│   │   │   ├── api.ts         # API クライアント
│   │   │   └── utils.ts       # ユーティリティ関数
│   │   ├── App.tsx            # メインコンポーネント
│   │   └── main.tsx           # エントリーポイント
│   ├── package.json           # Node.js 依存関係
│   ├── vite.config.ts         # Vite 設定
│   └── tailwind.config.js     # Tailwind CSS 設定
├── docs/
│   └── 金融市場監視システム設計.md
├── AGENTS.md
├── GEMINI.md
├── fx_dashboard.db            # SQLite データベース（実行時生成）
└── README.md
```

## 設定（実装完了後）

> **注意**: 以下の設定は実装が完了した後に適用されます。

### API キーの設定

`.env` ファイル（backend ディレクトリ）:

```env
# Claude API（ナラティブ生成）
CLAUDE_API_KEY=your_claude_api_key_here

# Gemini API（代替ナラティブ生成）
GEMINI_API_KEY=your_gemini_api_key_here
```

### データ更新頻度

- **価格データ**: 10分毎
- **相関分析**: 10分毎
- **重要レベル検出**: 10分毎
- **AIナラティブ**: セッション毎（1日3回: 東京、ロンドン、ニューヨーク開場時）

### ナラティブ生成タイミング

- **東京セッション**: 09:00 JST
- **ロンドンセッション**: 17:00 JST
- **ニューヨークセッション**: 22:00 JST

## 開発（実装完了後）

> **注意**: 以下の開発手順は実装が完了した後に有効になります。

### バックエンド開発

```bash
cd backend

# 開発モードで起動（自動リロード）
uvicorn src.main:app --reload

# テスト実行（今後追加予定）
pytest
```

### フロントエンド開発

```bash
cd frontend

# 開発サーバー起動
npm run dev

# 型チェック
npm run build

# Lint
npm run lint
```

## APIエンドポイント（実装完了後）

> **注意**: 以下のAPIエンドポイントは実装が完了した後に利用可能になります。

### 価格データ
- `GET /api/prices/weekly` - 週間価格サマリー
- `GET /api/prices/statistics` - 過去統計データ

### 相関分析
- `GET /api/correlations` - 相関資産データ

### セッション情報
- `GET /api/sessions/current` - 現在のセッション情報
- `GET /api/sessions/upcoming` - 今後のセッション

### ナラティブ
- `GET /api/narratives/latest` - 最新のナラティブ
- `POST /api/narratives/generate` - ナラティブ生成

### シナリオ
- `GET /api/scenarios` - 自動生成されたトレーディングシナリオ
- `GET /api/scenarios/levels` - 重要価格レベル

### アラート
- `GET /api/alerts/active` - アクティブなアラート
- `GET /api/alerts/upcoming` - 今後の予定アラート

### トレードログ
- `GET /api/trades` - トレード履歴
- `POST /api/trades` - 新規トレード記録
- `GET /api/trades/analytics` - パフォーマンス分析

詳細なAPIドキュメント: http://localhost:8000/docs

## ライセンス

このプロジェクトはプライベート使用を目的としています。

## 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-12-31 | 0.2.0 | README更新：MT5パッケージ詳細情報追加、プロジェクトステータス明確化 |
| 2025-12-30 | 0.1.0 | 実装開始（feature/initial-setupブランチ）、初期PRマージ |
| 2025-12-28 | 0.0.1 | 初版リリース（設計書とドキュメントのみ） |

**注**: バージョン1.0.0は実装が完了してmainブランチにマージされた後にリリース予定です。

## 参考資料

- [設計書](docs/金融市場監視システム設計.md) - 詳細な設計仕様
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [MetaTrader5 Python Package - PyPI](https://pypi.org/project/metatrader5/) - パッケージ情報とインストール方法
- [MetaTrader5 Python Integration - 公式ドキュメント](https://www.mql5.com/en/docs/python_metatrader5) - API リファレンス
- [MetaTrader5 Python インストールガイド](https://www.mql5.com/en/book/advanced/python/python_install) - セットアップ手順

---

**作成者**: Yasushi Fukutake
**プロジェクト名**: FX Discretionary Trading Cockpit
**対象通貨ペア**: USDJPY
