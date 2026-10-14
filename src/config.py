"""SportBot configuration module with zero hardcoded secrets policy."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    BOT_TOKEN: str = ""
    BOT_USERNAME: str = ""
    ADMIN_IDS: str = ""
    WEBAPP_URL: str = "http://localhost:3000"
    DATABASE_URL: str = "sqlite+aiosqlite:///data/sportbot.db"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    CYCLE_DAYS: int = 30
    LANGUAGE: str = "en"

    @property
    def admin_ids_list(self) -> list[int]:
        """Parse comma-separated ADMIN_IDS into a list of integer IDs."""
        if not self.ADMIN_IDS.strip():
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    def get_webapp_url(self, version: str = "1.0.0") -> str:
        """Generate TMA URL with cache-busting query parameter."""
        delimiter = "&" if "?" in self.WEBAPP_URL else "?"
        return f"{self.WEBAPP_URL}{delimiter}v={version}"


settings = Settings()
