from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str
    gemini_api_key: str
    gemini_model: str = "gemini-3.8-flash"
    gemini_fallback_model: str = "gemini-3.7-flash"
    gemini_emergency_model: str = "gemini-3.7-flash"
    gemini_first_token_timeout_ms: int = 2500
    gemini_request_timeout_ms: int = 15000
    gemini_model_cooldown_seconds: int = 30
    google_client_id: str
    session_secret: str
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False
settings = Settings()
