from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./jobs.db"

    # Ollama LLM
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:14b"
    llm_timeout: int = 120
    llm_threshold: int = 25
    llm_max_retries: int = 3
    llm_batch_size: int = 1

    # Notifications
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_email: str = ""
    smtp_password: str = ""

    # Scheduler
    auto_scrape_cron: str = "0 6 * * *"
    auto_evaluate_cron: str = "0 7 * * *"
    daily_report_cron: str = "0 8 * * *"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:5173"

    # Profile
    profile_path: str = "../user_profile.json"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
