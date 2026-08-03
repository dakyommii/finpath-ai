from types import SimpleNamespace

from models import FinancialProduct, Policy
from services.roadmap_service import generate_roadmap_steps


def _profile(**overrides):
    base = dict(
        age=27, annual_income=38000000, region="서울", marital_status="SINGLE",
        liquid_assets=20000000, total_debt=0, monthly_saving=1000000,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _seed_common_candidates(db_session):
    db_session.add_all(
        [
            Policy(
                title="청년내일저축계좌", category="청년자산형성",
                eligibility_rules={"age_min": 19, "age_max": 34}, benefit_info={},
            ),
            FinancialProduct(
                provider="테스트은행", title="테스트적금", category="적금",
                product_rules={}, rate_info={"max_rate": 4.0},
            ),
            Policy(
                title="청년전용 버팀목전세자금대출", category="대출",
                eligibility_rules={}, benefit_info={},
            ),
            Policy(
                title="신혼부부전용 전세자금대출", category="대출",
                eligibility_rules={}, benefit_info={},
            ),
            FinancialProduct(
                provider="테스트증권", title="테스트 ISA", category="ISA",
                product_rules={}, rate_info={},
            ),
            Policy(
                title="디딤돌대출(생애최초 주택구입)", category="대출",
                eligibility_rules={}, benefit_info={},
            ),
        ]
    )
    db_session.commit()


def test_emergency_fund_marked_completed_when_liquid_assets_sufficient(db_session):
    _seed_common_candidates(db_session)
    profile = _profile(liquid_assets=10_000_000)
    steps = generate_roadmap_steps(db_session, profile, goals=[], life_events=[])
    assert steps[0].title == "비상자금 확보"
    assert steps[0].status == "COMPLETED"


def test_emergency_fund_recommended_now_when_insufficient(db_session):
    _seed_common_candidates(db_session)
    profile = _profile(liquid_assets=1_000_000)
    steps = generate_roadmap_steps(db_session, profile, goals=[], life_events=[])
    assert steps[0].status == "RECOMMENDED_NOW"


def test_debt_repayment_step_included_only_when_debt_exists(db_session):
    _seed_common_candidates(db_session)
    with_debt = generate_roadmap_steps(db_session, _profile(total_debt=5_000_000), goals=[], life_events=[])
    without_debt = generate_roadmap_steps(db_session, _profile(total_debt=0), goals=[], life_events=[])

    assert any(s.title == "고금리 부채 상환" for s in with_debt)
    assert not any(s.title == "고금리 부채 상환" for s in without_debt)


def test_jeonse_and_home_purchase_stages_included_by_goal(db_session):
    _seed_common_candidates(db_session)
    goals = [SimpleNamespace(goal_type="JEONSE"), SimpleNamespace(goal_type="HOME_PURCHASE")]
    steps = generate_roadmap_steps(db_session, _profile(), goals=goals, life_events=[])
    titles = [s.title for s in steps]

    assert "전세자금 마련 준비" in titles
    assert "ISA를 통한 중장기 자산 운용" in titles
    assert "주택 구입 준비" in titles
    assert titles.index("전세자금 마련 준비") < titles.index("주택 구입 준비")


def test_marriage_life_event_prefers_newlywed_loan(db_session):
    _seed_common_candidates(db_session)
    goals = [SimpleNamespace(goal_type="JEONSE")]
    life_events = [SimpleNamespace(event_type="MARRIAGE")]
    steps = generate_roadmap_steps(db_session, _profile(), goals=goals, life_events=life_events)

    titles = [s.title for s in steps]
    assert "신혼부부 지원 검토" in titles

    jeonse_step = next(s for s in steps if s.title == "전세자금 마련 준비")
    assert jeonse_step.related_items
    assert "신혼부부" in jeonse_step.related_items[0]["title"]


def test_steps_have_sequential_non_overlapping_timeline(db_session):
    _seed_common_candidates(db_session)
    steps = generate_roadmap_steps(db_session, _profile(), goals=[], life_events=[])
    for prev, nxt in zip(steps, steps[1:]):
        assert nxt.recommended_start == prev.expected_end


def test_higher_monthly_saving_shortens_goal_stage_duration(db_session):
    """10.2 데모 시나리오의 전제: 월 저축액이 늘면 목표금액 관련 단계(주택 구입 준비)의
    소요기간이 "남은 목표금액 / 월 저축액"으로 짧아져야 한다."""
    _seed_common_candidates(db_session)
    goals = [SimpleNamespace(goal_type="HOME_PURCHASE", target_amount=100_000_000)]

    slower = generate_roadmap_steps(db_session, _profile(monthly_saving=1_000_000), goals=goals, life_events=[])
    faster = generate_roadmap_steps(db_session, _profile(monthly_saving=2_000_000), goals=goals, life_events=[])

    slower_end = next(s for s in slower if s.title == "주택 구입 준비").expected_end
    faster_end = next(s for s in faster if s.title == "주택 구입 준비").expected_end
    assert faster_end < slower_end


def test_stage_shows_up_to_three_eligible_candidates(db_session):
    db_session.add_all(
        [
            FinancialProduct(
                provider="A은행", title="A적금", category="적금",
                product_rules={}, rate_info={"max_rate": 5.0},
            ),
            FinancialProduct(
                provider="B은행", title="B적금", category="적금",
                product_rules={}, rate_info={"max_rate": 4.0},
            ),
            FinancialProduct(
                provider="C은행", title="C적금", category="적금",
                product_rules={}, rate_info={"max_rate": 3.0},
            ),
            FinancialProduct(
                provider="D은행", title="D적금", category="적금",
                product_rules={}, rate_info={"max_rate": 2.0},
            ),
        ]
    )
    db_session.commit()

    steps = generate_roadmap_steps(db_session, _profile(), goals=[], life_events=[])
    saving_step = next(s for s in steps if s.title == "월 자동저축 구조 설정")

    assert len(saving_step.related_items) == 3
    titles = [item["title"] for item in saving_step.related_items]
    assert titles == ["A적금", "B적금", "C적금"]


def test_goal_without_target_amount_falls_back_to_fixed_duration(db_session):
    _seed_common_candidates(db_session)
    goals = [SimpleNamespace(goal_type="HOME_PURCHASE", target_amount=None)]
    steps = generate_roadmap_steps(db_session, _profile(), goals=goals, life_events=[])
    home_step = next(s for s in steps if s.title == "주택 구입 준비")
    assert home_step.expected_end is not None
