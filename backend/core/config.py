from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://finpath:finpath@localhost:5432/finpath"
    llm_api_key: str = ""
    llm_api_base: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
