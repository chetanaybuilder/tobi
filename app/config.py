from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    groq_api_key: str
    groq_model: str = "openai/gpt-oss-120b"
    groq_fallback_model: str = "llama3-70b-8192"
    groq_emergency_model: str = "llama3-8b-8192"
    groq_first_token_timeout_ms: int = 2000
    groq_request_timeout_ms: int = 15000
    groq_model_cooldown_seconds: int = 30
    google_client_id: str
    session_secret: str
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False
settings = Settings()
