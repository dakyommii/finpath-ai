import os

# CI(GitHub Actions)는 표준 포트 5432의 postgres 서비스 컨테이너를 쓰므로 DATABASE_URL을
# 미리 넘겨준다. 로컬 개발 환경(이 머신은 5433번 포트 사용, README 참고)은 이 값이 없을 때만
# 기본값으로 5433을 쓰도록 해서 두 환경 모두에서 동작하게 한다.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg2://finpath:finpath@localhost:5433/finpath_test"
)

import pytest
from fastapi.testclient import TestClient

from core.db import Base, SessionLocal, engine
from main import app
from services.rag_service import clear_embedding_index_cache


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def clean_tables():
    yield
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
    # _build_index 캐시가 테스트 간에 남아있으면 이전 테스트의 정책/상품 데이터로
    # 만든 임베딩 인덱스를 다음 테스트가 그대로 재사용해버릴 수 있다.
    clear_embedding_index_cache()


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
