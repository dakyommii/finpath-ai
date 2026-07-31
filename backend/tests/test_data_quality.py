"""25장 평가 지표에 대응하는 회귀 검증.

- 추천 정확성: 자격조건 판별 시 확인 필요 조건이 누락되지 않는지
- 로드맵 품질: 12.2 선행관계를 위반하는 단계 순서가 나오지 않는지
- RAG 품질: 근거 문서가 연결된 단계에는 출처(sources)가 비어있지 않은지
"""

from types import SimpleNamespace

from models import FinancialProduct, Policy
from services.eligibility_service import EligibilityStatus, evaluate_policy
from services.roadmap_service import generate_roadmap_steps


def _profile(**overrides):
    base = dict(
        age=27, region="서울", job_status="EMPLOYED", annual_income=38000000,
        marital_status="SINGLE", housing_type="MONTHLY_RENT", liquid_assets=20000000,
        total_debt=0, monthly_saving=1000000, credit_score_band=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def test_conditional_status_always_carries_a_needs_confirmation_factor():
    """CONDITIONAL로 판정된 항목은 반드시 "확인 필요" 사유가 있어야 한다 (근거 없는
    조건부 판정이 나오지 않도록 하는 회귀 테스트)."""
    policy = SimpleNamespace(
        id="p1", title="무주택 지원 정책", eligibility_rules={"homeownership": "무주택"},
    )
    result = evaluate_policy(_profile(), policy)
    assert result.status == EligibilityStatus.CONDITIONAL
    assert "NEEDS_CONFIRMATION" in result.factors.values()


def test_roadmap_step_order_respects_12_2_dependency_chain(db_session):
    """12.2 선행관계: 비상자금 확보는 항상 부채상환/자산형성보다 먼저,
    전세자금 마련은 항상 주택구입 준비보다 먼저 나와야 한다."""
    db_session.add_all(
        [
            Policy(title="청년내일저축계좌", category="청년자산형성", eligibility_rules={}, benefit_info={}),
            Policy(title="청년전용 버팀목전세자금대출", category="대출", eligibility_rules={}, benefit_info={}),
            Policy(title="디딤돌대출(생애최초 주택구입)", category="대출", eligibility_rules={}, benefit_info={}),
        ]
    )
    db_session.commit()

    goals = [SimpleNamespace(goal_type="JEONSE"), SimpleNamespace(goal_type="HOME_PURCHASE")]
    profile = _profile(total_debt=3_000_000)
    steps = generate_roadmap_steps(db_session, profile, goals=goals, life_events=[])
    titles = [s.title for s in steps]

    assert titles.index("비상자금 확보") < titles.index("고금리 부채 상환")
    assert titles.index("고금리 부채 상환") < titles.index("청년 자산형성 상품 가입 검토")
    assert titles.index("전세자금 마련 준비") < titles.index("주택 구입 준비")


def test_steps_with_candidate_always_have_sources(db_session):
    """추천 후보가 연결된 단계는 반드시 출처(sources)가 함께 제공되어야 한다
    (26.2 근거 표시 요건)."""
    db_session.add(
        FinancialProduct(
            provider="테스트은행", title="테스트적금", category="적금",
            product_rules={}, rate_info={"max_rate": 3.0},
        )
    )
    db_session.commit()

    profile = _profile()
    steps = generate_roadmap_steps(db_session, profile, goals=[], life_events=[])
    for step in steps:
        if step.related_items:
            assert step.sources, f"'{step.title}' 단계에 추천 후보는 있지만 출처가 비어있음"
