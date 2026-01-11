"""
Application Configuration
中央集約的な設定管理
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):
    """アプリケーション設定"""

    # Database
    database_url: str = "sqlite+aiosqlite:///./fx_dashboard.db"
    db_echo: bool = False  # SQLログ出力（本番環境ではFalse推奨）

    # MT5
    mt5_symbol: str = "USDJPY"
    mt5_connection_timeout: float = 30.0
    mt5_operation_timeout: float = 10.0

    # Data Collection
    data_collection_interval_minutes: int = 10  # 10分ごと（README仕様に統一）

    # CORS
    cors_origins: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """
        CORS_ORIGINS を複数の形式で対応
        - JSON配列形式: '["http://localhost:5173", "http://localhost:3000"]'
        - カンマ区切り形式: 'http://localhost:5173,http://localhost:3000'
        """
        if isinstance(v, str):
            # JSON形式をチェック
            if v.startswith("["):
                try:
                    import json
                    return json.loads(v)
                except (json.JSONDecodeError, ValueError):
                    pass
            # カンマ区切り形式をパース
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    # API Keys (必須)
    gemini_api_key: str | None = None
    claude_api_key: str | None = None

    # Narrative Provider
    narrative_provider: str = "gemini"  # "gemini" or "claude"

    # Logging
    log_level: str = "INFO"
    log_file: str = "app.log"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5

    # Environment
    environment: str = "development"  # development, staging, production

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = False
        # 環境変数のプレフィックス（オプション）
        # env_prefix = "APP_"

    def validate_required_keys(self) -> None:
        """必須APIキーの検証"""
        if self.narrative_provider == "gemini" and not self.gemini_api_key:
            raise ValueError(
                "GEMINI_API_KEY is required when narrative_provider is 'gemini'. "
                "Please set it in your .env file."
            )
        if self.narrative_provider == "claude" and not self.claude_api_key:
            raise ValueError(
                "CLAUDE_API_KEY is required when narrative_provider is 'claude'. "
                "Please set it in your .env file."
            )

    @property
    def is_production(self) -> bool:
        """本番環境かどうか"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """開発環境かどうか"""
        return self.environment.lower() == "development"


# シングルトンインスタンス
settings = Settings()

# アプリケーション起動時に必須チェック
try:
    settings.validate_required_keys()
except ValueError as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.critical(f"Configuration Error: {e}")
    # 本番環境では起動を中止
    if os.getenv("ENVIRONMENT", "development").lower() == "production":
        raise
    else:
        logger.warning("Continuing in development mode despite missing API keys")
