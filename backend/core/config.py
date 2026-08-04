from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://finpath:finpath@localhost:5432/finpath"
    llm_api_key: str = ""
    llm_api_base: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    # "hashing"(기본값, 무료) | "local_semantic"(로컬 sentence-transformer, 메모리 사용량 큼).
    # Render 무료 티어(RAM 512MB)에서는 local_semantic으로 켜지 말 것 — OOM 위험.
    embedding_mode: str = "hashing"
    # 다국어 범용 모델(paraphrase-multilingual-MiniLM-L12-v2)로 실제 테스트했을 때 한국어
    # 금융/정책 짧은 문장에서는 무관한 문서가 관련 문서보다 더 높은 점수를 받는 경우가 있어,
    # 한국어 STS 특화 모델로 교체함 — 직접 비교 테스트에서 이 모델이 관련 정책을 명확히
    # 상위로 올바르게 랭킹함을 확인.
    local_embedding_model: str = "jhgan/ko-sroberta-multitask"
    env: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
