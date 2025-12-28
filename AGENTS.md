# Repository Guidelines

## Communication Language
**すべてのコミュニケーションは日本語で行ってください。**

このプロジェクトでは、以下すべてを日本語で統一します：
- コミットメッセージ
- Pull Request の説明
- Issue の報告
- コードコメント
- ドキュメント
- コードレビューのコメント

## エージェント運用ルール（確信度基準）

本ファイルは Codex CLI / Gemini CLI / Claude Code CLI の各エージェントが必ず参照する運用ルールです。

### 作業開始前のチェック

1. **ブランチ状態の確認**
   - ローカルおよびリモート（GitHub）のブランチ状態を確認
   - 衝突コンフリクト発生リスクがないことを必ずチェック
   - `git status` と `git branch -a` で現在の状態を把握

2. **最新コードの取得**
   ```bash
   git fetch origin
   git pull origin main
   ```

3. **作業ブランチの作成**（機能追加時）
   ```bash
   git checkout -b feature/説明的な名前
   ```

## テスト方針

### MQL5インジケーターのテスト

#### 手動テスト（必須）

1. **コンパイルテスト**
   ```
   MetaEditorで開く → F7でコンパイル → エラー・警告ゼロを確認
   ```

2. **動作テスト**
   - 複数の通貨ペア（USDJPY、EURUSD、GBPUSDなど）で確認
   - 複数のタイムフレーム（M1、M5、H1、D1）で確認
   - 過去チャートで表示が安定しているか確認
   - リアルタイムで更新されるか確認

3. **パラメータテスト**
   - デフォルト設定で動作確認
   - 極端な設定値での動作確認（エラーハンドリング）
   - アラート機能のテスト

4. **パフォーマンステスト**
   - 計算時間が許容範囲か確認
   - メモリ使用量のチェック
   - HistoryBarsを大きくした場合の動作

### Pythonモジュールのテスト（将来実装時）

#### フレームワーク
- **テストフレームワーク**: `pytest`
- **テストディレクトリ**: `tests/`
- **ファイル命名**: `test_*.py`

#### テストの種類

1. **単体テスト**
   - `utils.py` の関数テスト
   - ATR/ADX計算の不変条件チェック
   - `profit_factor` などの端ケーステスト
   - 数値計算の精度確認

2. **統合テスト**
   - データパイプライン全体のテスト
   - ラベリング処理の妥当性確認
   - 特徴量生成の正確性確認

3. **スモークテスト**
   - 各ステージの出力パス存在確認
   - 出力データの `shape > 0` を確認
   - 基本的な実行可能性の確認

4. **テストデータ**
   - 必要に応じ `tests/data/` に最小サンプルを追加
   - 実データは含めない（プライバシー保護）
   - 合成データまたは最小限のサンプル

#### テスト実行

```bash
# すべてのテストを実行
pytest -q

# 詳細表示
pytest -v

# 特定のテストファイルを実行
pytest tests/test_utils.py

# カバレッジ付き
pytest --cov=src tests/
```

## コミットと Pull Request

### コミット規約

**Conventional Commits形式を使用します（日本語）。**

#### 基本形式
```
<type>: <subject>

<body>（オプション）
```

#### タイプ

- `feat`: 新機能の追加
- `fix`: バグ修正
- `docs`: ドキュメントのみの変更
- `refactor`: リファクタリング（機能変更なし）
- `test`: テストの追加・修正
- `chore`: ビルド・設定の変更
- `perf`: パフォーマンス改善
- `style`: コードスタイルの修正（フォーマットのみ）

#### 例

```bash
# 良い例
git commit -m "feat: Convexityアラート機能を追加"
git commit -m "fix: Macro Lane の色表示を修正"
git commit -m "docs: ユーザーマニュアルにパラメータ説明を追加"
git commit -m "refactor: 方向性計算ロジックを整理"
git commit -m "test: ATR計算の単体テストを追加"

# 悪い例（英語）
git commit -m "feat: add donchian distance"  # ❌ 日本語で書く

# 悪い例（説明不足）
git commit -m "fix: bug"  # ❌ 何のバグか書く
git commit -m "update"    # ❌ 何を更新したか書く
```

### Pull Request 要件

PRを作成する際は、以下の情報を必ず含めてください：

1. **目的**
   - 何のための変更か
   - どの問題を解決するか

2. **変更概要**
   - 主要な変更点
   - 影響範囲

3. **関連Issue**
   - `Closes #123` や `Relates to #456` でリンク

4. **前後比較**（該当する場合）
   - パフォーマンス指標（PF、取引数など）
   - 動作の変化
   - スクリーンショット

5. **再現手順**
   - テストコマンド
   - 設定内容
   - 確認方法

6. **添付物**（オプション）
   - 小さなログ
   - 図・スクリーンショット
   - テスト結果

#### PRテンプレート例

```markdown
## 目的
Convexityアラート機能でクールダウン時間を設定可能にする

## 変更概要
- `ConvexityAlertCooldownHours` パラメータを追加
- 最後のアラート時刻を記録する `lastConvexityAlertTime` を実装
- クールダウン期間中は重複アラートを送信しない

## 関連Issue
Closes #45

## テスト
- [ ] MT5でコンパイル成功
- [ ] クールダウン24時間で重複通知されないことを確認
- [ ] クールダウン0時間で毎回通知されることを確認

## スクリーンショット
（パラメータ設定画面のスクリーンショット）
```

## セキュリティと設定

### 機密情報の管理

#### ❌ コミット禁止

- ブローカー情報（アカウント番号、サーバー名）
- APIキー、パスワード
- 個人の取引履歴
- 大容量の生データ（`data/raw/`）
- `.env` ファイル（環境変数）

#### ✅ `.gitignore` に追加

```gitignore
# データファイル
data/raw/
*.csv

# 環境設定
.env
credentials.json

# MT5固有
*.ex5
*.log

# Python
__pycache__/
*.pyc
.venv/
.pytest_cache/

# IDE
.vscode/
.idea/
*.swp
```

### データ管理

- **小さなサンプルデータ**: テスト用に最小限のデータのみコミット可
- **大容量データ**: ローカル保管のみ、Gitには含めない
- **機密データ**: 暗号化して別途管理

## コーディング規約

### MQL5コーディング規約

#### 命名規則

```mql5
// バッファ変数: xxxBuffer[]
double MacroLaneHighBuffer[];
double ConvexityColorBuffer[];

// ハンドル変数: hXxx_Yyy
int hMA_Fast_Meso;
int hADX_Macro;

// Enum: ENUM_XXX
enum ENUM_DIRECTION {
   DIR_NEUTRAL = 0,
   DIR_STRONG_UP
};

// 関数: PascalCase
void CalculateDirection() { }
int OnInit() { }

// Input変数: アンダースコア区切り
input int EMA_Fast_Period = 50;
input double ADX_Threshold = 20.0;

// ローカル変数: camelCase
int barCount = 0;
double priceValue = 0.0;
```

#### コメント規則

```mql5
//+------------------------------------------------------------------+
//| カスタムインジケーター初期化関数                                        |
//+------------------------------------------------------------------+
int OnInit()
  {
   // インジケーターバッファのマッピング
   SetIndexBuffer(0, MacroLaneHighBuffer, INDICATOR_DATA);

   // 固定レベルの設定
   PlotIndexSetDouble(0, PLOT_EMPTY_VALUE, 0.0);

   return(INIT_SUCCEEDED);
  }
```

#### インデント
- **スペース3つ**（MQL5標準）

#### ブレースの配置
```mql5
// 関数: 改行して配置
int OnInit()
  {
   // 処理
  }

// 制御文: 同じ行
if(condition) {
   // 処理
}
```

### Pythonコーディング規約（将来実装時）

#### 基本方針
- **PEP 8** に準拠
- **型ヒント** を使用
- **Docstring** を記述（Google形式またはNumPy形式）

#### 命名規則

```python
# 関数・変数: snake_case
def calculate_atr(prices: np.ndarray) -> float:
    pass

bar_count = 0
price_value = 0.0

# クラス: PascalCase
class StructureCalculator:
    pass

# 定数: UPPER_SNAKE_CASE
DEFAULT_ATR_PERIOD = 14
MAX_LOOKBACK_DAYS = 100

# プライベート: 先頭にアンダースコア
def _internal_helper():
    pass
```

#### Docstring

```python
def calculate_direction_score(
    fast_ema: float,
    slow_ema: float,
    price: float,
    adx: float
) -> float:
    """方向性スコアを計算する。

    Args:
        fast_ema: 高速EMAの値
        slow_ema: 低速EMAの値
        price: 現在価格
        adx: ADX値

    Returns:
        -1.0から+1.0の方向性スコア

    Raises:
        ValueError: 入力値が不正な場合
    """
    pass
```

#### インポート順序

```python
# 標準ライブラリ
import os
import sys
from datetime import datetime

# サードパーティ
import numpy as np
import pandas as pd

# ローカルモジュール
from src.utils import calculate_atr
from src.config import CONFIG
```

## 開発ワークフロー

### 1. 機能開発フロー

```bash
# 1. 最新コードを取得
git checkout main
git pull origin main

# 2. 機能ブランチを作成
git checkout -b feature/convexity-alert-cooldown

# 3. 開発・テスト
# （コードを書く）

# 4. コミット
git add .
git commit -m "feat: Convexityアラートにクールダウン機能を追加"

# 5. プッシュ
git push origin feature/convexity-alert-cooldown

# 6. Pull Request作成
# GitHubでPRを作成し、レビューを依頼
```

### 2. バグ修正フロー

```bash
# 1. バグ修正ブランチを作成
git checkout -b fix/macro-lane-color-issue

# 2. 修正・テスト
# （バグを修正）

# 3. コミット
git commit -m "fix: Macro Laneの色が正しく表示されない問題を修正"

# 4. プッシュ & PR
git push origin fix/macro-lane-color-issue
```

### 3. リリースフロー

```bash
# 1. バージョンを更新
# mt5/TimeStructureConvexityRail.mq5 の #property version を更新

# 2. コミット
git commit -m "chore: バージョンを1.02に更新"

# 3. タグを作成
git tag -a v1.02 -m "Release v1.02"

# 4. プッシュ
git push origin main --tags
```

## トラブルシューティング

### よくある問題

#### 1. MT5でインジケーターが表示されない

**原因**: データ読み込み中
**解決**: 数秒待ってチャートを更新（F5）

#### 2. コンパイルエラー

**原因**: 構文エラーまたは型の不一致
**解決**: エラーメッセージを確認し、該当行を修正

#### 3. Gitコンフリクト

**原因**: リモートとローカルの変更が競合
**解決**:
```bash
git fetch origin
git merge origin/main
# コンフリクトを手動で解決
git add .
git commit -m "merge: コンフリクトを解決"
```

## コミュニティ

### コントリビューションガイドライン

1. **Issue を確認**: 既存のIssueを確認し、重複を避ける
2. **ブランチを作成**: メインブランチから新しいブランチを作成
3. **小さなPR**: 1つのPRで1つの機能またはバグ修正
4. **テストを追加**: 新機能にはテストを追加
5. **ドキュメントを更新**: 必要に応じてドキュメントを更新
6. **レビューを待つ**: PRをマージする前にレビューを受ける

### コミュニケーション

- 📧 Email: info@convi.jp
- 💬 Issue: GitHubのIssueで質問・報告
- 📝 PR: Pull Requestでコードレビュー

---

**Happy Coding! 🚀**


