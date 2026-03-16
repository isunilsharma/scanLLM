"""
Application settings loaded from environment variables with YAML fallback.

Usage:
    from app.config import settings
"""
import os
from pathlib import Path
from typing import List, Optional

# Backend root directory (parent of app/)
BACKEND_DIR = Path(__file__).parent.parent
PROJECT_DIR = BACKEND_DIR.parent

# Try pydantic-settings first, fall back to plain class
try:
    from pydantic_settings import BaseSettings as _BaseSettings

    class Settings(_BaseSettings):
        """Application settings via pydantic-settings."""

        # Database
        DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BACKEND_DIR}/app.db")

        # Security
        SESSION_SECRET: str = "dev-secret-change-in-production"

        # GitHub OAuth
        GITHUB_CLIENT_ID: str = ""
        GITHUB_CLIENT_SECRET: str = ""
        GITHUB_REDIRECT_URI: str = "http://localhost:3000/auth/callback"

        # Frontend
        FRONTEND_URL: str = "http://localhost:3000"
        CORS_ORIGINS: str = "https://scanllm.ai,http://localhost:3000"

        # AI API keys
        ANTHROPIC_API_KEY: str = ""
        OPENAI_API_KEY: str = ""

        # Scan engine tuning
        SCAN_WORKERS: int = 4
        SCAN_FILE_LIMIT: int = 5000
        SCAN_MAX_FILE_SIZE: int = 500_000  # bytes

        # Token encryption
        TOKEN_ENCRYPTION_KEY: str = ""

        class Config:
            env_file = str(BACKEND_DIR / ".env")
            env_file_encoding = "utf-8"

except ImportError:
    # Fallback: plain class reading os.environ directly
    class Settings:  # type: ignore[no-redef]
        """Application settings loaded from environment variables."""

        def __init__(self) -> None:
            # Database
            self.DATABASE_URL: str = os.getenv(
                "DATABASE_URL", f"sqlite:///{BACKEND_DIR}/app.db"
            )

            # Security
            self.SESSION_SECRET: str = os.getenv(
                "SESSION_SECRET", "dev-secret-change-in-production"
            )

            # GitHub OAuth
            self.GITHUB_CLIENT_ID: str = os.getenv("GITHUB_CLIENT_ID", "")
            self.GITHUB_CLIENT_SECRET: str = os.getenv("GITHUB_CLIENT_SECRET", "")
            self.GITHUB_REDIRECT_URI: str = os.getenv(
                "GITHUB_REDIRECT_URI", "http://localhost:3000/auth/callback"
            )

            # Frontend
            self.FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
            self.CORS_ORIGINS: str = os.getenv(
                "CORS_ORIGINS", "https://scanllm.ai,http://localhost:3000"
            )

            # AI API keys
            self.ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
            self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

            # Scan engine tuning
            self.SCAN_WORKERS: int = int(os.getenv("SCAN_WORKERS", "4"))
            self.SCAN_FILE_LIMIT: int = int(os.getenv("SCAN_FILE_LIMIT", "5000"))
            self.SCAN_MAX_FILE_SIZE: int = int(
                os.getenv("SCAN_MAX_FILE_SIZE", "500000")
            )

            # Token encryption
            self.TOKEN_ENCRYPTION_KEY: str = os.getenv("TOKEN_ENCRYPTION_KEY", "")

            # Load YAML configs for backward compatibility
            self._yaml_config: Optional[object] = None
            self._load_yaml_configs()

        def _load_yaml_configs(self) -> None:
            """Load existing YAML configuration files for backward compat."""
            try:
                import sys
                sys.path.insert(0, str(BACKEND_DIR))
                from core.config import config as yaml_config

                self._yaml_config = yaml_config

                # Overlay YAML scan settings if they exist and env vars weren't set
                scan_settings = yaml_config.settings.get("scan", {})
                if os.getenv("SCAN_MAX_FILE_SIZE") is None and "max_file_size_bytes" in scan_settings:
                    self.SCAN_MAX_FILE_SIZE = scan_settings["max_file_size_bytes"]
            except Exception:
                # YAML configs are optional; env vars are sufficient
                pass

    @property  # type: ignore[misc]
    def cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a list."""
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


# Singleton instance
settings = Settings()
