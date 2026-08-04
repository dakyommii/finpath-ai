import math

from models import Policy
from services import rag_service
from services.rag_service import (
    EmbeddingProvider,
    LocalHashingEmbeddingProvider,
    get_embedding_provider,
    keyword_similarity_scores,
    retrieve_documents,
)


def test_local_embedding_is_unit_length():
    provider = LocalHashingEmbeddingProvider()
    vector = provider.embed("청년 자산형성 정책 지원")
    norm = math.sqrt(sum(v * v for v in vector))
    assert math.isclose(norm, 1.0, rel_tol=1e-6)


def test_local_embedding_is_deterministic():
    provider = LocalHashingEmbeddingProvider()
    assert provider.embed("동일한 문장") == provider.embed("동일한 문장")


def test_retrieve_documents_ranks_matching_policy_higher(db_session):
    db_session.add_all(
        [
            Policy(
                title="청년 전세자금 대출 지원",
                category="대출",
                description="무주택 청년의 전세 보증금 마련을 돕는 저리 대출 정책입니다.",
                eligibility_rules={},
                benefit_info={},
            ),
            Policy(
                title="산모신생아 건강관리 지원",
                category="출산양육지원",
                description="출산 가정에 건강관리사 방문 서비스를 지원합니다.",
                eligibility_rules={},
                benefit_info={},
            ),
        ]
    )
    db_session.commit()

    results = retrieve_documents(db_session, "전세 보증금 대출이 필요해요", top_k=2)

    assert results[0].title == "청년 전세자금 대출 지원"
    assert results[0].score >= results[1].score


def test_keyword_similarity_scores_empty_without_keywords(db_session):
    assert keyword_similarity_scores(db_session, []) == {}


def test_keyword_similarity_scores_empty_on_offline_fallback(db_session, monkeypatch):
    # 기본 상태(LLM_API_KEY 미설정)에서는 오프라인 해싱 폴백이 쓰이므로, 의미 유사도를
    # 계산할 수 없어 항상 빈 dict를 반환해야 한다(하위 호환 안전장치).
    monkeypatch.setattr("core.config.settings.llm_api_key", "changeme")
    db_session.add(
        Policy(title="이직 지원 정책", category="취업창업지원", eligibility_rules={}, benefit_info={})
    )
    db_session.commit()

    assert keyword_similarity_scores(db_session, ["이직 준비중"]) == {}


def test_keyword_similarity_scores_uses_real_provider_when_available(db_session, monkeypatch):
    # 실제 API 키가 있을 때의 동작을 가짜(semantic) 임베딩 provider로 검증한다.
    policy = Policy(
        title="이직/창업 지원 정책",
        category="취업창업지원",
        description="이직과 창업을 준비하는 청년을 지원합니다.",
        eligibility_rules={},
        benefit_info={},
    )
    unrelated = Policy(
        title="출산 지원금", category="출산양육지원", description="출산 가정 지원",
        eligibility_rules={}, benefit_info={},
    )
    db_session.add_all([policy, unrelated])
    db_session.commit()

    class FakeSemanticProvider(EmbeddingProvider):
        VOCAB = ["이직", "창업", "출산", "결혼"]

        def embed(self, text):
            return [1.0 if word in text else 0.0 for word in self.VOCAB]

    monkeypatch.setattr(rag_service, "get_embedding_provider", lambda: FakeSemanticProvider())

    scores = keyword_similarity_scores(db_session, ["이직 준비중"])

    assert scores[str(policy.id)] > scores[str(unrelated.id)]


def test_local_semantic_mode_falls_back_when_package_missing(monkeypatch):
    # sentence-transformers가 설치되어 있지 않은 환경(기본 requirements.txt만 설치된
    # CI/운영 환경)에서 EMBEDDING_MODE=local_semantic으로 설정해도 죽지 않고 해싱 폴백으로
    # 안전하게 넘어가야 한다. 이 머신에 패키지가 실제로 설치되어 있는지와 무관하게
    # 결정적으로 검증하기 위해 로더 자체가 ImportError를 던지도록 강제한다.
    monkeypatch.setattr("core.config.settings.llm_api_key", "changeme")
    monkeypatch.setattr("core.config.settings.embedding_mode", "local_semantic")

    def _raise_import_error():
        raise ImportError("sentence-transformers not installed")

    monkeypatch.setattr(rag_service, "_load_sentence_model", _raise_import_error)

    provider = get_embedding_provider()

    assert isinstance(provider, LocalHashingEmbeddingProvider)


def test_local_semantic_mode_selected_when_package_available(monkeypatch):
    from services.rag_service import LocalSentenceEmbeddingProvider

    monkeypatch.setattr("core.config.settings.llm_api_key", "changeme")
    monkeypatch.setattr("core.config.settings.embedding_mode", "local_semantic")
    monkeypatch.setattr(rag_service, "_load_sentence_model", lambda: object())

    provider = get_embedding_provider()

    assert isinstance(provider, LocalSentenceEmbeddingProvider)


def test_build_index_is_cached_per_provider_type(db_session):
    db_session.add(
        Policy(title="캐시 확인용 정책", category="청년자산형성", eligibility_rules={}, benefit_info={})
    )
    db_session.commit()

    first = rag_service._build_index(db_session, LocalHashingEmbeddingProvider())
    second = rag_service._build_index(db_session, LocalHashingEmbeddingProvider())

    assert first is second


def test_clear_embedding_index_cache_forces_rebuild(db_session):
    db_session.add(
        Policy(title="캐시 초기화 확인용 정책", category="청년자산형성", eligibility_rules={}, benefit_info={})
    )
    db_session.commit()

    first = rag_service._build_index(db_session, LocalHashingEmbeddingProvider())
    rag_service.clear_embedding_index_cache()
    second = rag_service._build_index(db_session, LocalHashingEmbeddingProvider())

    assert first is not second
    assert first == second
