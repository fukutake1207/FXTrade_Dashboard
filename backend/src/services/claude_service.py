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
        system_prompt = """You are a professional FX trader and analyst. 
Your job is to analyze the provided market data and generate a concise, professional market narrative for USDJPY.
Focus on:
1. Current trend and key levels.
2. Correlation with other assets (Gold, Nikkei, S&P500).
3. Market session context (Tokyo/London/NY).
4. Potential scenarios for the next few hours.

Keep the tone objective and professional. Use bullet points for clarity."""

        user_message = f"""
Current Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M')}
Market Data Summary:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

Please generate a market narrative based on this data.
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
