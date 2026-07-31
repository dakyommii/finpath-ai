import hashlib
import math
import re
from dataclasses import dataclass
from typing import Optional

import httpx

from core.config import settings

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


def _build_index(db, provider: EmbeddingProvider) -> list[dict]:
    from models import FinancialProduct, Policy

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
    return documents


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    # 두 벡터 모두 L2 정규화되어 있으므로 내적이 곧 코사인 유사도다.
    return sum(x * y for x, y in zip(a, b))


def retrieve_documents(db, query: str, top_k: int = 3) -> list[RetrievedDocument]:
    """정책/금융상품 설명 텍스트에서 질의와 가장 관련 있는 top_k개 문서를 반환한다.

    데이터 규모(정책+상품 약 50건)가 작아 매 호출마다 인덱스를 새로 구성해도 성능상 문제가
    없다. 데이터가 커지면 이 함수의 인덱스 구성 부분만 pgvector 등 외부 벡터 저장소로
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
