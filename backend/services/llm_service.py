import logging
import re
from typing import Optional

import httpx

from core.config import settings
from prompts.roadmap_explanation import ROADMAP_EXPLANATION_SYSTEM_PROMPT
from services.rag_service import RetrievedDocument

logger = logging.getLogger("finpath.llm")

NUMBER_PATTERN = re.compile(r"\d[\d,]*")


class LLMClient:
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


class OpenAICompatibleLLMClient(LLMClient):
    """실제 LLM 연동 (OpenAI 호환 /chat/completions 규격, 21장 기술스택 기준).

    주의: 이 개발 환경에는 유효한 API 키가 없어 실제 호출은 검증하지 못했다. 키 설정 후
    소규모로 먼저 확인할 것. 호출이 실패하면 explain_roadmap_step이 템플릿 설명으로
    안전하게 대체한다.
    """

    def __init__(self):
        self.api_key = settings.llm_api_key
        self.api_base = settings.llm_api_base

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = httpx.post(
            f"{self.api_base}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]


def get_llm_client() -> Optional[LLMClient]:
    if settings.llm_api_key and settings.llm_api_key != "changeme":
        return OpenAICompatibleLLMClient()
    return None


def _build_user_prompt(step_title: str, step_action: str, completion_condition: str,
                        retrieved_docs: list[RetrievedDocument]) -> str:
    sources = "\n".join(f"- {d.title} (출처: {d.official_url or '확인 필요'})" for d in retrieved_docs) or "관련 문서 없음"
    return (
        f"단계명: {step_title}\n"
        f"기본 행동: {step_action}\n"
        f"완료 조건: {completion_condition}\n"
        f"검색된 관련 공식 문서:\n{sources}\n"
    )


def _template_explanation(step_title: str, step_action: str, completion_condition: str,
                           retrieved_docs: list[RetrievedDocument]) -> str:
    """LLM_API_KEY가 없을 때 사용하는 오프라인 폴백. 16.1 프롬프트가 요구하는 항목을
    구조화된 입력값만으로 채우며, 문서에 없는 수치나 조건은 만들어내지 않는다."""
    lines = [f"이 단계가 필요한 이유: {step_action}", f"해야 할 행동: {step_title}"]
    if retrieved_docs:
        top = retrieved_docs[0]
        lines.append(f"참고할 수 있는 관련 정보: {top.title} (공식 출처: {top.official_url or '확인 필요'})")
    else:
        lines.append("현재 조건에 정확히 맞는 공식 문서를 찾지 못해 신청 전 별도 확인이 필요합니다.")
    lines.append(f"완료 조건: {completion_condition}")
    lines.append("주의사항: 실제 신청 가능 여부와 금리·지원금액은 공식 기관을 통해 다시 확인해야 합니다.")
    return " ".join(lines)


def _flag_unsupported_numbers(explanation: str, retrieved_docs: list[RetrievedDocument], trusted_text: str = "") -> None:
    """26.3 환각 방지: 설명문에 등장한 숫자가 근거 문서나 Rule Engine이 이미 정한 신뢰
    텍스트(trusted_text: 단계 행동/완료조건 등) 어디에도 없으면 경고 로그를 남긴다.
    서비스를 막지는 않고(하드 실패 없음), 운영 중 모니터링을 위한 경고만 남긴다."""
    source_text = trusted_text + " " + " ".join(d.text for d in retrieved_docs)
    for number in NUMBER_PATTERN.findall(explanation):
        if number not in source_text:
            logger.warning("LLM 설명에 근거 문서에서 확인되지 않는 수치가 포함됨: %s", number)


def explain_roadmap_step(step_title: str, step_action: str, completion_condition: str,
                          retrieved_docs: list[RetrievedDocument]) -> str:
    trusted_text = f"{step_title} {step_action} {completion_condition}"
    client = get_llm_client()
    if client is None:
        explanation = _template_explanation(step_title, step_action, completion_condition, retrieved_docs)
        _flag_unsupported_numbers(explanation, retrieved_docs, trusted_text)
        return explanation

    try:
        user_prompt = _build_user_prompt(step_title, step_action, completion_condition, retrieved_docs)
        explanation = client.complete(ROADMAP_EXPLANATION_SYSTEM_PROMPT, user_prompt)
    except Exception:
        logger.exception("LLM 호출 실패, 템플릿 설명으로 대체합니다.")
        explanation = _template_explanation(step_title, step_action, completion_condition, retrieved_docs)

    _flag_unsupported_numbers(explanation, retrieved_docs, trusted_text)
    return explanation
