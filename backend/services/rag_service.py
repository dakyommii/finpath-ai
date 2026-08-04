import hashlib
import logging
import math
import re
from dataclasses import dataclass
from typing import Optional

import httpx

from core.config import settings

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 256


class EmbeddingProvider:
    def embed(self, text: str) -> list[float]:
        raise NotImplementedError


class LocalHashingEmbeddingProvider(EmbeddingProvider):
    """API 키 없이 동작하는 오프라인 폴백 임베딩.

    문자 2-gram을 해시 버킷에 매핑해 L2 정규화한 벡터를 만든다. 의미 기반 임베딩(BGE-M3,
    OpenAI 등)보다 품질은 떨어지지만, 외부 API 없이도 RAG 파이프라인 전체를 동작·검증할 수
    있게 해준다. pgvector도 이 macOS 환경에서 설치가 막혀 있어(README 참고), 유사도 계산은
    DB가 아닌 애플리케이션 계층에서 수행한다. LLM_API_KEY가 실제 값으로 설정되면
    OpenAIEmbeddingProvider로 자동 전환된다.
    """

    def __init__(self, dim: int = EMBEDDING_DIM):
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dim
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        bigrams = [normalized[i : i + 2] for i in range(len(normalized) - 1)] or [normalized]
        for bigram in bigrams:
            bucket = int(hashlib.md5(bigram.encode("utf-8")).hexdigest(), 16) % self.dim
            vector[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        return [v / norm for v in vector]


_sentence_model = None


def _load_sentence_model():
    global _sentence_model
    if _sentence_model is None:
        from sentence_transformers import SentenceTransformer

        _sentence_model = SentenceTransformer(settings.local_embedding_model)
    return _sentence_model


class LocalSentenceEmbeddingProvider(EmbeddingProvider):
    """API 키 없이 진짜 의미 기반 임베딩을 계산하는 로컬 provider.

    한국어 STS 특화 sentence-transformer(기본 jhgan/ko-sroberta-multitask)를 CPU에서 돌려
    실제 의미 유사도를 잡아낸다(LocalHashingEmbeddingProvider와 달리 동의어/유사 표현도
    매칭 가능). 다국어 범용 모델(paraphrase-multilingual-MiniLM-L12-v2)로도 시도했으나 실제
    비교 테스트에서 한국어 금융/정책 짧은 문장에는 순위를 잘 못 매겨(무관한 정책이 관련
    정책보다 높은 점수를 받는 경우 발생) 한국어 특화 모델로 교체했다.

    대신 torch를 포함한 무거운 의존성(requirements-embedding.txt로 별도 설치)과 첫 호출 시
    모델 로딩 비용이 들고, 실측 기준 프로세스 메모리를 약 700MB 이상 점유한다. Render 무료
    티어(RAM 512MB)에서는 확실히 OOM으로 죽으므로, EMBEDDING_MODE 설정으로 명시적으로 켠
    경우에만 사용된다 (core/config.py 참고). 최소 1GB 이상 메모리가 보장되는 환경에서만
    켤 것.
    """

    def embed(self, text: str) -> list[float]:
        model = _load_sentence_model()
        vector = model.encode(text, normalize_embeddings=True)
        return vector.tolist()


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """실제 임베딩 API 연동. LLM_API_KEY가 설정된 경우에만 사용된다.

    주의: 이 개발 환경에는 유효한 API 키가 없어 실제 호출은 검증하지 못했다. OpenAI
    Embeddings API 규격에 맞춰 작성했으니, 키 설정 후 소규모로 먼저 확인할 것.
    """

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.api_base = settings.llm_api_base
        self.model = settings.embedding_model

    def embed(self, text: str) -> list[float]:
        response = httpx.post(
            f"{self.api_base}/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": text},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]


def get_embedding_provider() -> EmbeddingProvider:
    if settings.llm_api_key and settings.llm_api_key != "changeme":
        return OpenAIEmbeddingProvider()
    if settings.embedding_mode == "local_semantic":
        try:
            _load_sentence_model()
            return LocalSentenceEmbeddingProvider()
        except ImportError:
            logger.warning(
                "EMBEDDING_MODE=local_semantic이지만 sentence-transformers가 설치되어 있지 않아 "
                "해싱 폴백으로 전환합니다. pip install -r requirements-embedding.txt 로 설치하세요."
            )
    return LocalHashingEmbeddingProvider()


@dataclass
class RetrievedDocument:
    item_type: str
    item_id: str
    title: str
    text: str
    official_url: Optional[str]
    last_verified_at: Optional[str]
    score: float


def _document_text(title: str, category: str, description: Optional[str], benefit_info: Optional[dict]) -> str:
    parts = [title, category, description or ""]
    if benefit_info:
        parts.append(" ".join(str(v) for v in benefit_info.values() if isinstance(v, (str, int, float))))
    return " ".join(p for p in parts if p)


_index_cache: dict[str, list[dict]] = {}


def clear_embedding_index_cache() -> None:
    """정책/상품 데이터를 다시 씨딩했거나 테스트에서 격리가 필요할 때 캐시를 비운다."""
    _index_cache.clear()


def _build_index(db, provider: EmbeddingProvider) -> list[dict]:
    from models import FinancialProduct, Policy

    # 정책/상품 카탈로그는 자주 바뀌지 않는데, 임베딩 계산(특히 local_semantic)은 요청마다
    # 다시 하기엔 비싸다. provider 종류별로 프로세스 생애주기 동안 한 번만 계산해 재사용한다.
    cache_key = type(provider).__name__
    cached = _index_cache.get(cache_key)
    if cached is not None:
        return cached

    documents = []
    for policy in db.query(Policy).all():
        text = _document_text(policy.title, policy.category, policy.description, policy.benefit_info)
        documents.append(
            {
                "item_type": "POLICY",
                "item_id": str(policy.id),
                "title": policy.title,
                "text": text,
                "official_url": policy.official_url,
                "last_verified_at": policy.last_verified_at.isoformat() if policy.last_verified_at else None,
                "embedding": provider.embed(text),
            }
        )
    for product in db.query(FinancialProduct).all():
        text = _document_text(product.title, product.category, None, product.benefit_info)
        documents.append(
            {
                "item_type": "FINANCIAL_PRODUCT",
                "item_id": str(product.id),
                "title": product.title,
                "text": text,
                "official_url": product.official_url,
                "last_verified_at": product.last_verified_at.isoformat() if product.last_verified_at else None,
                "embedding": provider.embed(text),
            }
        )
    _index_cache[cache_key] = documents
    return documents


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    # 두 벡터 모두 L2 정규화되어 있으므로 내적이 곧 코사인 유사도다.
    return sum(x * y for x, y in zip(a, b))


def keyword_similarity_scores(db, keywords: list[str]) -> dict[str, float]:
    """사용자가 온보딩에서 선택한 관심사 키워드와 각 정책/금융상품 문서 간 코사인 유사도.

    Scoring Engine의 goal_relevance에 보조 신호로 블렌딩하기 위한 함수다 (키워드 임베딩
    추천 보강 설계 문서 4.2/4.3 참고). 오프라인 해싱 폴백(LocalHashingEmbeddingProvider)은
    문자 겹침만 볼 뿐 의미를 이해하지 못해 이 용도로는 부적합하므로, 그 경우 빈 dict를
    반환한다 — 호출부(scoring_service)는 빈 dict를 받으면 기존 하드코딩 표 점수만 쓰도록
    설계되어 있어 API 키 없이도 항상 안전하게 동작한다. local_semantic 모드
    (LocalSentenceEmbeddingProvider)나 OpenAI 임베딩은 실제 의미를 잡아내므로 정상적으로
    블렌딩에 사용된다.
    """
    if not keywords:
        return {}
    provider = get_embedding_provider()
    if isinstance(provider, LocalHashingEmbeddingProvider):
        return {}

    interest_vector = provider.embed(" ".join(keywords))
    index = _build_index(db, provider)
    return {doc["item_id"]: _cosine_similarity(interest_vector, doc["embedding"]) for doc in index}


def retrieve_documents(db, query: str, top_k: int = 3) -> list[RetrievedDocument]:
    """정책/금융상품 설명 텍스트에서 질의와 가장 관련 있는 top_k개 문서를 반환한다.

    인덱스는 provider별로 프로세스 생애주기 동안 캐시된다(_build_index 참고) — local_semantic
    모드처럼 임베딩 계산 비용이 큰 경우에도 매 요청마다 카탈로그 전체를 다시 인코딩하지
    않는다. 데이터가 커지면 이 함수의 인덱스 구성 부분만 pgvector 등 외부 벡터 저장소로
    교체하면 된다 (retrieve_documents의 시그니처는 그대로 유지 가능).
    """
    provider = get_embedding_provider()
    query_vector = provider.embed(query)
    index = _build_index(db, provider)

    scored = [
        RetrievedDocument(
            item_type=doc["item_type"],
            item_id=doc["item_id"],
            title=doc["title"],
            text=doc["text"],
            official_url=doc["official_url"],
            last_verified_at=doc["last_verified_at"],
            score=_cosine_similarity(query_vector, doc["embedding"]),
        )
        for doc in index
    ]
    scored.sort(key=lambda d: d.score, reverse=True)
    return scored[:top_k]
