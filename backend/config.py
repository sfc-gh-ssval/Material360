from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Values come from environment variables or a local .env file (see .env.example)
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parent.parent / ".env",
        extra="ignore",
    )

    snowflake_connection_name: str = "default"  # entry in ~/.snowflake/connections.toml
    snowflake_warehouse: str = "COMPUTE_WH"
    snowflake_database: str = "SNOWFLAKE_INTELLIGENCE"
    snowflake_schema: str = "ENGINEERING_DRAWINGS"
    stage_name: str = "DRAWING_STAGE"
    search_service: str = "DRAWING_SEARCH"
    model_name: str = "claude-sonnet-4-6"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

settings = Settings()
