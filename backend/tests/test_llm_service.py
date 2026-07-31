import logging

from services.llm_service import (
    OpenAICompatibleLLMClient,
    _flag_unsupported_numbers,
    explain_roadmap_step,
    get_llm_client,
)
from services.rag_service import RetrievedDocument


def test_get_llm_client_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr("core.config.settings.llm_api_key", "changeme")
    assert get_llm_client() is None


def test_get_llm_client_returns_openai_compatible_client_with_key(monkeypatch):
    monkeypatch.setattr("core.config.settings.llm_api_key", "sk-test-key")
    client = get_llm_client()
    assert isinstance(client, OpenAICompatibleLLMClient)


def test_explain_roadmap_step_offline_fallback_covers_required_elements(monkeypatch):
    monkeypatch.setattr("core.config.settings.llm_api_key", "changeme")
    doc = RetrievedDocument(
        item_type="POLICY",
        item_id="p1",
        title="청년내일채움공제",
        text="청년내일채움공제 청년자산형성 2년형 기준 본인 400만원 납입",
        official_url="https://example.gov.kr/policy/youth-fill-savings",
        last_verified_at="2026-07-31T00:00:00",
        score=0.9,
    )
    explanation = explain_roadmap_step(
        step_title="청년 자산형성 상품 가입 검토",
        step_action="정부 매칭 지원이 있는 자산형성 상품 가입을 검토합니다.",
        completion_condition="가입 완료 및 월 납입액 설정",
        retrieved_docs=[doc],
    )

    assert "가입 완료 및 월 납입액 설정" in explanation
    assert "청년내일채움공제" in explanation
    assert "공식 기관" in explanation


def test_flag_unsupported_numbers_warns_when_number_not_in_sources(caplog):
    doc = RetrievedDocument(
        item_type="POLICY", item_id="p1", title="정책A", text="정책A 지원 내용",
        official_url=None, last_verified_at=None, score=0.5,
    )
    with caplog.at_level(logging.WARNING, logger="finpath.llm"):
        _flag_unsupported_numbers("이 상품은 최대 9999만원까지 지원됩니다.", [doc])

    assert any("9999" in record.message for record in caplog.records)


def test_flag_unsupported_numbers_silent_when_number_in_sources(caplog):
    doc = RetrievedDocument(
        item_type="POLICY", item_id="p1", title="정책A", text="정책A 최대 600만원 지원",
        official_url=None, last_verified_at=None, score=0.5,
    )
    with caplog.at_level(logging.WARNING, logger="finpath.llm"):
        _flag_unsupported_numbers("이 상품은 최대 600만원까지 지원됩니다.", [doc])

    assert len(caplog.records) == 0
