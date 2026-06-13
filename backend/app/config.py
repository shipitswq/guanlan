from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./stock_sim.db"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4o"
    cache_ttl_hours: int = 6

    class Config:
        env_file = ".env"

settings = Settings()
