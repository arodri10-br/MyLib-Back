from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "MyLib Back"
    ENV: str = "dev"
    # SQLite default (mantém compatível com seu projeto atual)
    DATABASE_URL: str = Field(default="sqlite:///./mylib.db")

    # JWT
    JWT_SECRET_KEY: str = Field(default="CHANGE_ME_SUPER_SECRET")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRES_MINUTES: int = Field(default=60 * 12)  # 12h

    # Seed admin (cria/atualiza na inicialização)
    ADMIN_USERNAME: str = Field(default="admin")
    ADMIN_PASSWORD: str = Field(default="admin123")
    ADMIN_EMAIL: str = Field(default="admin@example.com")

settings = Settings()
