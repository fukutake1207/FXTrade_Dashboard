import os
import httpx
from typing import Dict, Any, Optional
from datetime import datetime
import json

# Assuming we might run this where 'anthropic' pkg isn't installed yet, 
# using httpx for raw API call is safer given the environment issues,
# but using the SDK is standard. Let's use httpx to be dependency-light 
# or assume the user will install 'anthropic'. 
# For this code, I'll use direct HTTP calls to minimize dependency friction 
# in the broken python environment context, but structured like a service.

class ClaudeService:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-5-sonnet-20240620"
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

客観的かつプロフェッショナルなトーンで記述してください。
必ず日本語で出力してください。見出し・箇条書きも日本語にしてください。"""

        user_message = f"""
現在の日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}
市場データサマリー:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

このデータに基づいて市場ナラティブを作成してください。
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
