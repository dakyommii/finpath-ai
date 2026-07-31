from types import SimpleNamespace

from models import FinancialProduct, Policy
from services.roadmap_service import generate_roadmap_steps
from services.simulation_service import simulate_roadmap


def _profile(**overrides):
    base = dict(
        age=27, region="서울", job_status="EMPLOYED", annual_income=38000000,
        marital_status="SINGLE", housing_type="MONTHLY_RENT", liquid_assets=20000000,
        total_debt=0, monthly_saving=1000000, credit_score_band=None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _seed_candidates(db_session):
    db_session.add_all(
        [
            Policy(title="청년내일저축계좌", category="청년자산형성", eligibility_rules={}, benefit_info={}),
            FinancialProduct(provider="테스트은행", title="테스트적금", category="적금", product_rules={}),
            Policy(title="청년전용 버팀목전세자금대출", category="대출", eligibility_rules={}, benefit_info={}),
            Policy(title="신혼부부전용 전세자금대출", category="대출", eligibility_rules={}, benefit_info={}),
            FinancialProduct(provider="테스트증권", title="테스트 ISA", category="ISA", product_rules={}),
            Policy(title="디딤돌대출(생애최초 주택구입)", category="대출", eligibility_rules={}, benefit_info={}),
        ]
    )
    db_session.commit()


class _FakeRoadmap:
    def __init__(self, steps, estimated_completion_date):
        self.steps = steps
        self.estimated_completion_date = estimated_completion_date


def _build_baseline_roadmap(db_session, profile, goals, life_events):
    steps = generate_roadmap_steps(db_session, profile, goals, life_events)
    return _FakeRoadmap(steps, steps[-1].expected_end if steps else None)


def test_higher_monthly_saving_does_not_delay_completion(db_session):
    _seed_candidates(db_session)
    goals = [SimpleNamespace(goal_type="HOME_PURCHASE")]
    profile = _profile()
    roadmap = _build_baseline_roadmap(db_session, profile, goals, [])

    result = simulate_roadmap(db_session, roadmap, profile, goals, [], monthly_saving=1_200_000)

    assert result.simulated_estimated_completion_date <= result.original_estimated_completion_date
    assert result.months_saved is not None and result.months_saved >= 0


def test_marriage_life_event_adds_step_in_simulation(db_session):
    _seed_candidates(db_session)
    goals = [SimpleNamespace(goal_type="JEONSE")]
    profile = _profile()
    roadmap = _build_baseline_roadmap(db_session, profile, goals, [])

    marriage_event = SimpleNamespace(event_type="MARRIAGE")
    result = simulate_roadmap(db_session, roadmap, profile, goals, [], extra_life_events=[marriage_event])

    assert "신혼부부 지원 검토" in result.added_steps
    assert result.removed_steps == []


def test_no_changes_yields_no_diff(db_session):
    _seed_candidates(db_session)
    goals = [SimpleNamespace(goal_type="SEED_MONEY")]
    profile = _profile()
    roadmap = _build_baseline_roadmap(db_session, profile, goals, [])

    result = simulate_roadmap(db_session, roadmap, profile, goals, [])

    assert result.added_steps == []
    assert result.removed_steps == []
    assert result.simulated_estimated_completion_date == result.original_estimated_completion_date
