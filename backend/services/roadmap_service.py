import math
from dataclasses import dataclass
from datetime import date
from typing import Optional

from rules.roadmap_dependencies import build_stage_sequence
from services.eligibility_service import EligibilityStatus
from services.scoring_service import score_and_rank

EMERGENCY_FUND_TARGET = 6_000_000

# 목표금액을 채워야 하는 단계(전세자금 마련/주택구입 준비)는 "남은 목표금액 ÷ 월 저축액"으로
# 소요기간을 계산한다. 그 외 단계는 stage 템플릿의 고정 소요기간을 그대로 쓴다.
SAVINGS_DRIVEN_STAGES = {
    "JEONSE_PREP": "JEONSE",
    "HOME_PURCHASE_PREP": "HOME_PURCHASE",
}


def _savings_driven_duration_months(stage_key: str, profile, goals) -> Optional[int]:
    goal_type = SAVINGS_DRIVEN_STAGES.get(stage_key)
    if not goal_type or not profile.monthly_saving:
        return None
    goal = next((g for g in goals if g.goal_type == goal_type and getattr(g, "target_amount", None)), None)
    if goal is None:
        return None
    remaining = max(goal.target_amount - profile.liquid_assets, 0)
    return max(1, math.ceil(remaining / profile.monthly_saving))


def _add_months(d: date, months: int) -> date:
    total_month_index = d.month - 1 + months
    year = d.year + total_month_index // 12
    month = total_month_index % 12 + 1
    day = min(d.day, 28)
    return date(year, month, day)


@dataclass
class RoadmapStepDraft:
    order: int
    title: str
    status: str
    recommended_start: date
    expected_end: date
    action: str
    reason: str
    completion_condition: str
    related_items: list[dict]
    sources: list[dict]


MAX_CANDIDATES_PER_STAGE = 3


def _select_candidates(ranked, categories, title_keywords=None, prefer_keyword=None, limit=MAX_CANDIDATES_PER_STAGE):
    if not categories:
        return []
    pool = [
        r
        for r in ranked
        if r.category in categories and r.eligibility_status != EligibilityStatus.NOT_ELIGIBLE
    ]
    if title_keywords:
        keyword_matches = [r for r in pool if any(kw in r.title for kw in title_keywords)]
        if keyword_matches:
            pool = keyword_matches
    if prefer_keyword:
        preferred = [r for r in pool if prefer_keyword in r.title]
        others = [r for r in pool if prefer_keyword not in r.title]
        pool = preferred + others
    return pool[:limit]


def generate_roadmap_steps(db, profile, goals, life_events, keywords=None) -> list[RoadmapStepDraft]:
    """12.1의 1~8단계(목표 분류 ~ 예상 실행시점 계산)를 수행해 로드맵 단계 초안을 만든다.

    자연어 설명 다듬기(12.1의 10단계, LLM)는 Phase 9에서 별도로 처리하며, 이 함수는
    Rule/Scoring Engine 결과만으로 결정되는 구조화된 단계만 생성한다. keywords는 온보딩에서
    선택한 관심사 키워드로, Scoring Engine의 goal_relevance 보정에만 쓰인다(단계 구성 자체는
    build_stage_sequence가 profile/goals/life_events만으로 그대로 결정).
    """
    ranked = score_and_rank(db, profile, goals, life_events, keywords)
    stages = build_stage_sequence(profile, goals, life_events)

    steps: list[RoadmapStepDraft] = []
    cursor = date.today()
    first_incomplete_assigned = False

    for order, stage in enumerate(stages, start=1):
        candidates = _select_candidates(ranked, stage.categories, stage.title_keywords, stage.prefer_keyword)

        completed = stage.key == "EMERGENCY_FUND" and profile.liquid_assets >= EMERGENCY_FUND_TARGET

        duration_months = _savings_driven_duration_months(stage.key, profile, goals) or stage.duration_months
        recommended_start = cursor
        expected_end = _add_months(cursor, duration_months)
        cursor = expected_end

        if completed:
            status = "COMPLETED"
        elif not first_incomplete_assigned:
            status = "RECOMMENDED_NOW"
            first_incomplete_assigned = True
        else:
            status = "PLANNED"

        related_items = []
        sources = []
        reason = stage.action_template
        if candidates:
            primary = candidates[0]
            related_items = [
                {"item_type": c.item_type, "item_id": c.item_id, "title": c.title} for c in candidates
            ]
            sources = [
                {"item_type": primary.item_type, "item_id": primary.item_id, "title": primary.title}
            ]
            reason = f"{stage.action_template} 추천 상품: {primary.title} ({primary.reason})"
        elif stage.categories:
            reason = f"{stage.action_template} 현재 조건에 맞는 상품을 찾지 못해 조건 변경 시 다시 확인이 필요합니다."

        steps.append(
            RoadmapStepDraft(
                order=order,
                title=stage.title,
                status=status,
                recommended_start=recommended_start,
                expected_end=expected_end,
                action=stage.action_template,
                reason=reason,
                completion_condition=stage.completion_condition,
                related_items=related_items,
                sources=sources,
            )
        )

    return steps


def enrich_steps_with_explanations(db, steps: list[RoadmapStepDraft]) -> None:
    """12.1의 10단계: RAG로 관련 공식 문서를 검색하고 LLM(또는 오프라인 폴백)으로 각 단계의
    설명을 사용자용 자연어로 다듬는다. Rule/Scoring/Roadmap Engine이 정한 단계 순서·후보는
    바꾸지 않고 텍스트(reason)와 출처(sources)만 보강한다. steps를 제자리에서 갱신한다.
    """
    from services.llm_service import explain_roadmap_step
    from services.rag_service import retrieve_documents

    for step in steps:
        # 이미 Rule/Scoring Engine이 후보를 골라둔 경우, 그 후보명으로 검색해야 RAG가
        # 인용하는 문서와 실제 추천 후보(related_items)가 일치한다. 후보가 없을 때만
        # 단계 제목으로 검색한다.
        query = step.related_items[0]["title"] if step.related_items else step.title
        retrieved = retrieve_documents(db, query, top_k=2)
        step.reason = explain_roadmap_step(step.title, step.action, step.completion_condition, retrieved)

        existing_ids = {item["item_id"] for item in step.sources}
        for doc in retrieved:
            if doc.item_id not in existing_ids:
                step.sources.append(
                    {
                        "item_type": doc.item_type,
                        "item_id": doc.item_id,
                        "title": doc.title,
                        "official_url": doc.official_url,
                        "last_verified_at": doc.last_verified_at,
                    }
                )
                existing_ids.add(doc.item_id)


def current_stage_and_progress(steps: list[RoadmapStepDraft]):
    if not steps:
        return None, 0.0
    completed = sum(1 for s in steps if s.status == "COMPLETED")
    progress = completed / len(steps)
    current = next((s for s in steps if s.status != "COMPLETED"), steps[-1])
    return current.title, progress
