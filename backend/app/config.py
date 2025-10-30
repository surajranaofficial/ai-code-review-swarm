"""Configuration management for Tiger Cloud and AI services"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Tiger Cloud Database
    tiger_service_id: str
    tiger_db_host: str
    tiger_db_port: int = 5432
    tiger_db_name: str = "tsdb"
    tiger_db_user: str = "tsdbadmin"
    tiger_db_password: str
    
    # AI Provider Keys
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    
    # App Config
    app_env: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # GitHub
    github_token: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"
    
    @property
    def database_url(self) -> str:
        """Generate PostgreSQL connection URL"""
        return (
            f"postgresql://{self.tiger_db_user}:{self.tiger_db_password}"
            f"@{self.tiger_db_host}:{self.tiger_db_port}/{self.tiger_db_name}"
        )
    
    @property
    def async_database_url(self) -> str:
        """Generate async PostgreSQL connection URL"""
        return (
            f"postgresql+asyncpg://{self.tiger_db_user}:{self.tiger_db_password}"
            f"@{self.tiger_db_host}:{self.tiger_db_port}/{self.tiger_db_name}"
        )


settings = Settings()
