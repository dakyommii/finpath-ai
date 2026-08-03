from types import SimpleNamespace

from services.eligibility_service import EligibilityStatus, evaluate_policy


def _profile(**overrides):
    base = dict(age=27, annual_income=38000000, region="서울", marital_status="SINGLE", special_status=[])
    base.update(overrides)
    return SimpleNamespace(**base)


class _Policy:
    def __init__(self, id, title, eligibility_rules):
        self.id = id
        self.title = title
        self.eligibility_rules = eligibility_rules


def test_age_exceeded_not_eligible():
    policy = _Policy("p1", "청년정책", {"age_min": 19, "age_max": 34})
    result = evaluate_policy(_profile(age=40), policy)
    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert result.factors["age"] == "NOT_MET"


def test_age_below_minimum_not_eligible():
    policy = _Policy("p1b", "청년정책", {"age_min": 19, "age_max": 34})
    result = evaluate_policy(_profile(age=18), policy)
    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert result.factors["age"] == "NOT_MET"


def test_income_exceeded_not_eligible():
    policy = _Policy("p2", "저소득지원", {"income_max": 30000000})
    result = evaluate_policy(_profile(annual_income=50000000), policy)
    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert result.factors["income"] == "NOT_MET"


def test_region_mismatch_not_eligible():
    policy = _Policy("p3", "서울청년정책", {"region": ["서울"]})
    result = evaluate_policy(_profile(region="부산"), policy)
    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert result.factors["region"] == "NOT_MET"


def test_marital_status_mismatch_not_eligible():
    policy = _Policy("p4", "신혼부부지원", {"marital_status": ["MARRIED"]})
    result = evaluate_policy(_profile(marital_status="SINGLE"), policy)
    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert result.factors["marital_status"] == "NOT_MET"


def test_all_conditions_met_eligible():
    policy = _Policy(
        "p5",
        "청년정책",
        {"age_min": 19, "age_max": 34, "income_max": 50000000, "region": ["서울"]},
    )
    result = evaluate_policy(_profile(), policy)
    assert result.status == EligibilityStatus.ELIGIBLE
    assert all(v in ("MET", "NOT_APPLICABLE") for v in result.factors.values())


def test_homeownership_never_inferred_needs_confirmation():
    policy = _Policy("p6", "무주택지원", {"homeownership": "무주택"})
    result = evaluate_policy(_profile(), policy)
    assert result.status == EligibilityStatus.CONDITIONAL
    assert result.factors["homeownership"] == "NEEDS_CONFIRMATION"


def test_no_rules_defaults_to_eligible():
    policy = _Policy("p7", "제한없음", {})
    result = evaluate_policy(_profile(), policy)
    assert result.status == EligibilityStatus.ELIGIBLE


def test_target_group_mismatch_not_eligible():
    policy = _Policy("p8", "국가유공자지원", {"target_group": ["국가유공자"]})
    result = evaluate_policy(_profile(special_status=[]), policy)
    assert result.status == EligibilityStatus.NOT_ELIGIBLE
    assert result.factors["target_group"] == "NOT_MET"


def test_target_group_match_eligible():
    policy = _Policy("p9", "국가유공자지원", {"target_group": ["국가유공자"]})
    result = evaluate_policy(_profile(special_status=["국가유공자"]), policy)
    assert result.status == EligibilityStatus.ELIGIBLE
    assert result.factors["target_group"] == "MET"


def test_target_group_not_specified_is_not_applicable():
    policy = _Policy("p10", "일반정책", {})
    result = evaluate_policy(_profile(special_status=["장애인"]), policy)
    assert result.factors["target_group"] == "NOT_APPLICABLE"
