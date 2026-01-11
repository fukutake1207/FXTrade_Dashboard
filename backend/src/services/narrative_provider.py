"""
Narrative Provider Management

設定ファイルベースのプロバイダー管理
ランタイムでの変更は設定ファイルに反映され、次回起動時に有効になります。
"""
from ..config import settings
import logging
import os

logger = logging.getLogger(__name__)


def get_provider() -> str:
    """現在のナラティブプロバイダーを取得"""
    return settings.narrative_provider


def set_provider(provider: str) -> str:
    """
    ナラティブプロバイダーを設定

    注意: この変更は現在のセッションのみ有効です。
    永続化するには.envファイルを更新してください。

    Args:
        provider: "gemini" または "claude"

    Returns:
        設定されたプロバイダー名
    """
    provider = provider.lower()
    if provider not in ("gemini", "claude"):
        raise ValueError("provider must be 'gemini' or 'claude'")

    # APIキーの存在確認
    if provider == "gemini" and not settings.gemini_api_key:
        raise ValueError("GEMINI_API_KEY is not configured")
    if provider == "claude" and not settings.claude_api_key:
        raise ValueError("CLAUDE_API_KEY is not configured")

    # 現在のセッションで設定を更新
    settings.narrative_provider = provider
    logger.info(f"Narrative provider changed to: {provider}")

    # 将来的な改善: .envファイルを自動更新する機能を追加できます
    logger.info(
        f"To persist this change, update NARRATIVE_PROVIDER={provider} in your .env file"
    )

    return provider
