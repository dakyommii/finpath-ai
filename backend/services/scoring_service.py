import json
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from services.eligibility_service import (
    EligibilityStatus,
    evaluate_financial_product,
    evaluate_policy,
)

WEIGHTS = {
    "eligibility": 0.35,
    "goal_relevance": 0.25,
    "benefit": 0.15,
    "urgency": 0.10,
    "risk_reduction": 0.10,
    "life_event_relevance": 0.05,
}

# 목표 유형(7.1 "목표정보": 전세·주택·목돈·부채상환)별로 각 카테고리가 얼마나 관련 있는지를
# 나타내는 휴리스틱 가중치(0~1). 실제 금액/효용 기반 최적화가 아닌 MVP용 근사치이며,
# 표에 없는 조합은 DEFAULT_RELEVANCE를 사용한다.
DEFAULT_RELEVANCE = 0.3
GOAL_CATEGORY_RELEVANCE = {
    "JEONSE": {
        "대출": 1.0, "주거비지원": 0.8, "신혼부부지원": 0.6,
        "청년자산형성": 0.4, "청년자산형성계좌": 0.4, "적금": 0.3, "예금": 0.3,
    },
    "HOME_PURCHASE": {
        "대출": 1.0, "청년자산형성": 0.6, "청년자산형성계좌": 0.6, "ISA": 0.5,
        "주거비지원": 0.5, "신혼부부지원": 0.6, "적금": 0.4,
    },
    "SEED_MONEY": {
        "청년자산형성": 1.0, "청년자산형성계좌": 1.0, "적금": 0.9, "지역청년지원": 0.7,
        "ISA": 0.7, "예금": 0.6, "단기자금관리상품": 0.5,
    },
    "DEBT_REPAYMENT": {
        "단기자금관리상품": 0.4, "대출": 0.3, "예금": 0.3, "적금": 0.3,
        "청년자산형성": 0.2,
    },
}

# 7.5 "부채 및 주거 위험 감소 효과"에 대한 카테고리별 휴리스틱
RISK_REDUCTION_BY_CATEGORY = {
    "주거비지원": 0.8, "대출": 0.7, "신혼부부지원": 0.5,
    "단기자금관리상품": 0.3, "지역청년지원": 0.3, "청년자산형성": 0.3, "청년자산형성계좌": 0.3,
    "취업창업지원": 0.2, "출산양육지원": 0.2, "적금": 0.2, "예금": 0.2, "ISA": 0.2,
    "연금저축": 0.1,
}
DEFAULT_RISK_REDUCTION = 0.3

LIFE_EVENT_CATEGORY_MAP = {
    "MARRIAGE": {"신혼부부지원", "주거비지원"},
    "CHILDBIRTH": {"출산양육지원"},
    "RELOCATION": {"주거비지원", "대출"},
    "JOB_CHANGE": {"취업창업지원"},
}

# 대출성 정책은 보통 한 목적에 한 상품만 실제로 이용 가능하므로, 같은 카테고리 내
# 1순위를 제외한 나머지에 중복/상충 감점을 적용한다 (7.5 Conflict Penalty).
MUTUALLY_EXCLUSIVE_CATEGORIES = {"대출"}
CONFLICT_PENALTY = 0.15

AMOUNT_PATTERN = re.compile(r"(\d[\d,]*)\s*만원")
URGENCY_FULL_WINDOW_DAYS = 90


def eligibility_component(status: EligibilityStatus) -> float:
    return {
        EligibilityStatus.ELIGIBLE: 1.0,
        EligibilityStatus.CONDITIONAL: 0.5,
        EligibilityStatus.NOT_ELIGIBLE: 0.0,
    }[status]


def goal_relevance_component(goal_types: list[str], category: str) -> float:
    if not goal_types:
        return DEFAULT_RELEVANCE
    return max(
        GOAL_CATEGORY_RELEVANCE.get(goal_type, {}).get(category, DEFAULT_RELEVANCE)
        for goal_type in goal_types
    )


def benefit_component(item_type: str, benefit_info, rate_info) -> float:
    if item_type == "FINANCIAL_PRODUCT" and rate_info and rate_info.get("max_rate"):
        return min(rate_info["max_rate"] / 6.0, 1.0)
    if benefit_info:
        text = json.dumps(benefit_info, ensure_ascii=False)
        amounts = [int(a.replace(",", "")) for a in AMOUNT_PATTERN.findall(text)]
        if amounts:
            return min(max(amounts) / 1000, 1.0)
    return 0.3


def urgency_component(application_end, today: Optional[date] = None) -> float:
    if not application_end:
        return 0.3
    today = today or date.today()
    days_left = (application_end - today).days
    if days_left < 0:
        return 0.0
    return max(0.0, min(1.0, 1 - days_left / URGENCY_FULL_WINDOW_DAYS))


def risk_reduction_component(category: str) -> float:
    return RISK_REDUCTION_BY_CATEGORY.get(category, DEFAULT_RISK_REDUCTION)


def life_event_relevance_component(life_event_types: list[str], category: str) -> float:
    for event_type in life_event_types:
        if category in LIFE_EVENT_CATEGORY_MAP.get(event_type, set()):
            return 1.0
    return 0.0


@dataclass
class RankedRecommendation:
    item_type: str
    item_id: str
    title: str
    category: str
    eligibility_status: EligibilityStatus
    eligibility_factors: dict[str, str]
    score_breakdown: dict[str, float] = field(default_factory=dict)
    conflict_penalty: float = 0.0
    priority_score: float = 0.0
    reason: str = ""
    benefit_info: Optional[dict] = None
    application_end: Optional[date] = None
    official_url: Optional[str] = None


def _build_reason(status: EligibilityStatus, breakdown: dict[str, float]) -> str:
    top_factor = max(
        (k for k in breakdown if k != "eligibility"),
        key=lambda k: breakdown[k],
    )
    factor_labels = {
        "goal_relevance": "목표 연관성",
        "benefit": "예상 혜택",
        "urgency": "신청 시급성",
        "risk_reduction": "위험 감소 효과",
        "life_event_relevance": "생애이벤트 연관성",
    }
    return f"{status.value} · 주요 근거: {factor_labels.get(top_factor, top_factor)}"


def _score_candidate(item_type, item_id, title, category, eligibility_status, eligibility_factors,
                      benefit_info, rate_info, application_end, official_url,
                      goal_types, life_event_types) -> RankedRecommendation:
    breakdown = {
        "eligibility": eligibility_component(eligibility_status),
        "goal_relevance": goal_relevance_component(goal_types, category),
        "benefit": benefit_component(item_type, benefit_info, rate_info),
        "urgency": urgency_component(application_end),
        "risk_reduction": risk_reduction_component(category),
        "life_event_relevance": life_event_relevance_component(life_event_types, category),
    }
    weighted_sum = sum(breakdown[k] * WEIGHTS[k] for k in WEIGHTS)
    return RankedRecommendation(
        item_type=item_type,
        item_id=item_id,
        title=title,
        category=category,
        eligibility_status=eligibility_status,
        eligibility_factors=eligibility_factors,
        score_breakdown=breakdown,
        priority_score=weighted_sum,
        reason=_build_reason(eligibility_status, breakdown),
        benefit_info=benefit_info,
        application_end=application_end,
        official_url=official_url,
    )


def _apply_conflict_penalty(candidates: list[RankedRecommendation]) -> None:
    by_category: dict[str, list[RankedRecommendation]] = {}
    for c in candidates:
        if c.category in MUTUALLY_EXCLUSIVE_CATEGORIES:
            by_category.setdefault(c.category, []).append(c)

    for group in by_category.values():
        group.sort(key=lambda c: c.priority_score, reverse=True)
        for c in group[1:]:
            c.conflict_penalty = CONFLICT_PENALTY
            c.priority_score = max(0.0, c.priority_score - CONFLICT_PENALTY)
            c.reason += " · 동일 목적 상품 중복 가능성으로 우선순위 조정됨"


def score_and_rank(db, profile, goals=None, life_events=None) -> list[RankedRecommendation]:
    from models import FinancialProduct, Policy

    goal_types = [g.goal_type for g in (goals or [])]
    life_event_types = [e.event_type for e in (life_events or [])]

    candidates: list[RankedRecommendation] = []

    for policy in db.query(Policy).all():
        result = evaluate_policy(profile, policy)
        candidates.append(
            _score_candidate(
                item_type="POLICY",
                item_id=result.item_id,
                title=result.title,
                category=policy.category,
                eligibility_status=result.status,
                eligibility_factors=result.factors,
                benefit_info=policy.benefit_info,
                rate_info=None,
                application_end=policy.application_end,
                official_url=policy.official_url,
                goal_types=goal_types,
                life_event_types=life_event_types,
            )
        )

    for product in db.query(FinancialProduct).all():
        result = evaluate_financial_product(profile, product)
        candidates.append(
            _score_candidate(
                item_type="FINANCIAL_PRODUCT",
                item_id=result.item_id,
                title=result.title,
                category=product.category,
                eligibility_status=result.status,
                eligibility_factors=result.factors,
                benefit_info=product.benefit_info,
                rate_info=product.rate_info,
                application_end=None,
                official_url=product.official_url,
                goal_types=goal_types,
                life_event_types=life_event_types,
            )
        )

    _apply_conflict_penalty(candidates)
    candidates.sort(key=lambda c: c.priority_score, reverse=True)
    return candidates
