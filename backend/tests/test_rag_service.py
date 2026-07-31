import math

from models import Policy
from services.rag_service import LocalHashingEmbeddingProvider, retrieve_documents


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
