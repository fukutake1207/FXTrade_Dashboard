import os
import httpx
import json
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self):
        # Attempt to load key from environment
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # If not found, try to find and load .env explicitly
        if not self.api_key:
            from dotenv import load_dotenv, find_dotenv
            env_file = find_dotenv()
            if env_file:
                logger.info(f"GeminiService: Key not found, reloading .env from {env_file}")
                load_dotenv(env_file)
                self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
             logger.info("GeminiService: GEMINI_API_KEY loaded successfully.")
        else:
             logger.error("GeminiService: GEMINI_API_KEY NOT found even after explicit reload.")

        # Using gemini-3-flash-preview
        self.model = "gemini-3-flash-preview"
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate_market_narrative(self, context_data: Dict[str, Any]) -> str:
        if not self.api_key:
            return "Error: GEMINI_API_KEY not found in environment variables."

        # Construct the prompt (Logic reused from ClaudeService but adapted if needed)
        # Using a combined prompt for Gemini might be simpler as it supports system instructions 
        # but simple user prompt is robust enough for REST.
        
        system_instruction_text = """あなたはプロフェッショナルなFXトレーダー兼アナリストです。
提供された市場データを分析し、USDJPY（ドル円）に関する簡潔で専門的な市場ナラティブ（相場解説）を日本語で作成してください。
以下の点に焦点を当ててください：
1. 現在のトレンドと重要な価格レベル（レジスタンス・サポート）。
2. 他の資産（ゴールド、日経平均、S&P500）との相関関係。
3. 市場セッションのコンテキスト（東京/ロンドン/NY時間）。
4. 今後数時間のシナリオと戦略。

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

        # Gemini REST API Format
        # URL: https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent
        url = f"{self.base_url}/{self.model}:generateContent?key={self.api_key}"
        
        headers = {
            "Content-Type": "application/json"
        }

        # Payload structure:
        # {
        #   "contents": [{
        #     "parts": [{"text": "..."}]
        #   }],
        #   "system_instruction": { "parts": [{"text": "..."}] } # Supported in 1.5-flash
        # }
        
        payload = {
            "system_instruction": {
                "parts": [
                    {"text": system_instruction_text}
                ]
            },
            "contents": [
                {
                    "parts": [
                        {"text": user_message} 
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 4096
            }
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload, timeout=30.0)
                
                if response.status_code != 200:
                    logger.error(f"Gemini API Error: {response.status_code} - {response.text}")
                    return f"API Error: {response.status_code} - {response.text}"
                
                data = response.json()
                # Parse response
                # Structure: data['candidates'][0]['content']['parts'][0]['text']
                try:
                    content = data['candidates'][0]['content']['parts'][0]['text']
                    return content
                except (KeyError, IndexError) as e:
                    logger.error(f"Failed to parse Gemini response: {data}")
                    return "Error: Failed to parse AI response."
                
        except Exception as e:
            logger.error(f"Failed to connect to Gemini API: {str(e)}")
            return f"Failed to generate narrative: {str(e)}"

# Singleton instance
gemini_service = GeminiService()
