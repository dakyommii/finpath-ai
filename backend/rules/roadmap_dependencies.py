from dataclasses import dataclass
from typing import Optional


@dataclass
class StageSpec:
    key: str
    title: str
    categories: list[str]
    completion_condition: str
    duration_months: int
    action_template: str
    title_keywords: Optional[list[str]] = None
    prefer_keyword: Optional[str] = None


def _has_goal(goals, goal_type: str) -> bool:
    return any(g.goal_type == goal_type for g in goals)


def _has_life_event(life_events, event_type: str) -> bool:
    return any(e.event_type == event_type for e in life_events)


def build_stage_sequence(profile, goals, life_events) -> list[StageSpec]:
    """12.1의 1~8단계(후보 생성~실행시점 계산)에 해당하는 단계 순서를 구성한다.

    12.2 선행관계(비상자금 확보 → 부채상환 → 자산형성 → 전세자금 → 주택구입)를 기본
    골격으로 하되, 사용자 목표(goals)와 생애 이벤트(life_events)에 따라 단계를
    추가/제외한다. 모든 사용자에게 동일한 순서를 강제하지 않는다는 12.2 원칙을 따른다.
    """
    is_married_soon = _has_life_event(life_events, "MARRIAGE")
    stages: list[StageSpec] = []

    stages.append(
        StageSpec(
            key="EMERGENCY_FUND",
            title="비상자금 확보",
            categories=["예금", "단기자금관리상품"],
            completion_condition="비상자금 600만원 확보",
            duration_months=3,
            action_template="생활비 6개월분(약 600만원)을 비상자금으로 확보합니다.",
        )
    )

    if profile.total_debt and profile.total_debt > 0:
        stages.append(
            StageSpec(
                key="DEBT_REPAYMENT",
                title="고금리 부채 상환",
                categories=[],
                completion_condition="고금리 부채 전액 상환",
                duration_months=6,
                action_template="상환 부담이 큰 고금리 부채부터 우선 정리합니다.",
            )
        )

    stages.append(
        StageSpec(
            key="SEED_MONEY_BUILDING",
            title="청년 자산형성 상품 가입 검토",
            categories=["청년자산형성", "청년자산형성계좌"],
            completion_condition="가입 완료 및 월 납입액 설정",
            duration_months=1,
            action_template="정부 매칭 지원이 있는 자산형성 상품 가입을 검토합니다.",
        )
    )

    stages.append(
        StageSpec(
            key="AUTO_SAVING_SETUP",
            title="월 자동저축 구조 설정",
            categories=["적금"],
            completion_condition="자동이체 등록 완료",
            duration_months=1,
            action_template="월 저축 가능액만큼 자동이체 저축 구조를 설정합니다.",
        )
    )

    if is_married_soon:
        stages.append(
            StageSpec(
                key="MARRIAGE_PREP",
                title="신혼부부 지원 검토",
                categories=["신혼부부지원"],
                completion_condition="지원 대상 여부 확인 및 신청 서류 준비",
                duration_months=2,
                action_template="혼인 예정에 따라 신혼부부 대상 주거·자산 지원을 확인합니다.",
            )
        )

    if _has_goal(goals, "JEONSE"):
        stages.append(
            StageSpec(
                key="JEONSE_PREP",
                title="전세자금 마련 준비",
                categories=["대출", "주거비지원"],
                completion_condition="전세 보증금 목표의 30% 확보, 대출 자격요건 재확인",
                duration_months=12,
                action_template="전세자금대출 자격을 사전 점검하고 보증금을 마련합니다.",
                title_keywords=["전세"],
                prefer_keyword="신혼" if is_married_soon else None,
            )
        )

    if _has_goal(goals, "HOME_PURCHASE") or _has_goal(goals, "SEED_MONEY"):
        stages.append(
            StageSpec(
                key="MID_TERM_ASSET_GROWTH",
                title="ISA를 통한 중장기 자산 운용",
                categories=["ISA"],
                completion_condition="ISA 계좌 개설 및 정기납입 설정",
                duration_months=1,
                action_template="비과세 한도를 활용해 중장기 자금을 ISA로 운용합니다.",
            )
        )

    if _has_goal(goals, "HOME_PURCHASE"):
        stages.append(
            StageSpec(
                key="HOME_PURCHASE_PREP",
                title="주택 구입 준비",
                categories=["대출"],
                completion_condition="목표금액 달성 및 정책대출 자격 확인",
                duration_months=24,
                action_template="목표금액을 채우고 생애최초·신혼부부 정책대출을 검토합니다.",
                title_keywords=["디딤돌", "보금자리", "희망타운", "구입"],
                prefer_keyword="신혼" if is_married_soon else None,
            )
        )

    return stages
