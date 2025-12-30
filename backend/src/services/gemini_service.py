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

        # User requested gemini-2.5-flash initally, then 3.0 if working.
        # We start with 2.5-flash as requested.
        self.model = "gemini-2.5-flash" 
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate_market_narrative(self, context_data: Dict[str, Any]) -> str:
        if not self.api_key:
            return "Error: GEMINI_API_KEY not found in environment variables."

        # Construct the prompt (Logic reused from ClaudeService but adapted if needed)
        # Using a combined prompt for Gemini might be simpler as it supports system instructions 
        # but simple user prompt is robust enough for REST.
        
        system_instruction = """あなたはプロフェッショナルなFXトレーダー兼アナリストです。
提供された市場データを分析し、USDJPY（ドル円）に関する簡潔で専門的な市場ナラティブ（相場解説）を日本語で作成してください。
以下の点に焦点を当ててください：
1. 現在のトレンドと重要な価格レベル（レジスタンス・サポート）。
2. 他の資産（ゴールド、日経平均、S&P500）との相関関係。
3. 市場セッションのコンテキスト（東京/ロンドン/NY時間）。
4. 今後数時間のシナリオと戦略。

トーンは客観的かつ専門的に保ってください。箇条書きを使用して明確に記述してください。"""

        user_message = f"""
Current Date/Time: {context_data.get('timestamp', 'N/A')}
Market Data Summary:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

Please generate a market narrative based on this data.
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
        #   "system_instruction": { "parts": [{"text": "..."}] } # Optional, supported in newer models
        # }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"{system_instruction}\n\n---\n\n{user_message}"} 
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000
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
