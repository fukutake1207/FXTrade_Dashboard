import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import json
import logging

# Assuming we might run this where 'anthropic' pkg isn't installed yet,
# using httpx for raw API call is safer given the environment issues,
# but using the SDK is standard. Let's use httpx to be dependency-light
# or assume the user will install 'anthropic'.
# For this code, I'll use direct HTTP calls to minimize dependency friction
# in the broken python environment context, but structured like a service.

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-haiku-4-5-20251001"
        self.api_url = "https://api.anthropic.com/v1/messages"

    async def generate_market_narrative(self, context_data: Dict[str, Any]) -> str:
        if not self.api_key:
            return "Error: ANTHROPIC_API_KEY not found in environment variables."

        # Construct the prompt
        system_prompt = """あなたはプロのFXアナリストです。
USDJPYの市場データを分析し、簡潔で実用的なナラティブを作成してください。
以下の点に焦点を当ててください：
1. 現在のトレンドと重要な価格レベル。
2. 他の資産（ゴールド、日経平均、S&P500）との相関。
3. 市場セッション（東京/ロンドン/NY）の状況。
4. 今後数時間のシナリオ。

**【絶対遵守】出力形式の指示:**
- マークダウン記号（#, *, -, ```など）は一切使用禁止
- 必ずHTMLタグのみを使用してください
- 見出しは <h2>または<h3>を使用し、セクションを明確に分ける
- 各セクションの後には必ず説明の段落<p>を追加
- 箇条書きは簡潔に、1項目1行で記述
- 重要な数値や用語は<strong>で強調
- トレンドや方向性は<em>で強調
- 価格レベル（レジスタンス・サポート・ピボット）は以下の形式で表示:
  <strong style="color: #6366f1; background-color: rgba(99, 102, 241, 0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace;">156.75円</strong>
- 最初の文字から必ず<h2>で始めてください

**構造の推奨:**
1. 市場概況（現在の価格、トレンド）
2. 重要な価格レベル（サポート・レジスタンス）
3. 相関関係（ゴールド、日経、S&P500）
4. 市場セッション
5. シナリオと戦略

出力例：
<h2>📊 市場概況</h2>
<p>USDJPY は現在 <strong>150.25円</strong> で推移しており、<em>上昇トレンド</em>を継続しています。本日の値幅は <strong>0.45円</strong> と比較的狭い範囲で推移しています。</p>

<h3>🎯 重要な価格レベル</h3>
<ul>
<li><strong>レジスタンス:</strong> 150.50円（日足レジスタンス）</li>
<li><strong>サポート:</strong> 149.00円（前日安値）</li>
<li><strong>ピボット:</strong> 149.75円</li>
</ul>

<h3>🔗 相関関係</h3>
<p>ゴールドは<em>弱い逆相関</em>（相関係数: <strong>-0.35</strong>）を示しており、ドル高の影響を受けています。日経平均との相関は<strong>0.62</strong>とやや強い正の相関が見られます。</p>

HTML文書全体は不要で、コンテンツ部分のみのHTMLフラグメントとして出力してください。絵文字を使って視覚的に分かりやすくしてください。"""

        # Extract USDJPY price for emphasis
        usdjpy_price = context_data.get('usdjpy_current_price', {})
        usdjpy_mid = usdjpy_price.get('mid', 0)

        user_message = f"""
【重要】提供される時刻は日本時間（JST, UTC+9）です。

現在の日時: {context_data.get('timestamp', 'N/A')}

**【最重要】USDJPY現在価格:**
- Bid: {usdjpy_price.get('bid', 'N/A')}円
- Ask: {usdjpy_price.get('ask', 'N/A')}円
- Mid: {usdjpy_mid}円

**必ず上記のUSDJPY現在価格（{usdjpy_mid}円付近）を基準にして、現実的な価格レベル（レジスタンス・サポート・ピボット）を計算してください。**
架空の価格や過去の知識に基づく価格は使用せず、提供された現在価格から±1円〜3円程度の範囲で重要価格レベルを設定してください。

市場データサマリー:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

このデータに基づいて市場ナラティブを作成してください。
現在時刻は日本時間であることを念頭に、東京/ロンドン/NYセッションの判断を行ってください。
"""

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_message}
            ]
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.api_url, headers=headers, json=payload, timeout=30.0)
                
                if response.status_code != 200:
                    return f"API Error: {response.status_code} - {response.text}"

                data = response.json()
                content = data['content'][0]['text']
                return content
                
        except Exception as e:
            return f"Failed to generate narrative: {str(e)}"

claude_service = ClaudeService()
