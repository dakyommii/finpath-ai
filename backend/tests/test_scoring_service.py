from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from models import FinancialProduct, Policy
from services.scoring_service import goal_relevance_component, score_and_rank


def _profile(**overrides):
    base = dict(age=27, annual_income=38000000, region="서울", marital_status="SINGLE")
    base.update(overrides)
    return SimpleNamespace(**base)


def test_goal_relevance_ranks_matching_category_higher(db_session):
    seed_money_policy = Policy(
        title="자산형성 정책",
        category="청년자산형성",
        eligibility_rules={},
        benefit_info={},
    )
    unrelated_policy = Policy(
        title="양육 지원 정책",
        category="출산양육지원",
        eligibility_rules={},
        benefit_info={},
    )
    db_session.add_all([seed_money_policy, unrelated_policy])
    db_session.commit()

    goal = SimpleNamespace(goal_type="SEED_MONEY")
    ranked = score_and_rank(db_session, _profile(), goals=[goal], life_events=[])

    titles_in_order = [r.title for r in ranked]
    assert titles_in_order.index("자산형성 정책") < titles_in_order.index("양육 지원 정책")


def test_not_eligible_ranks_below_eligible(db_session):
    eligible = Policy(
        title="적격 정책",
        category="청년자산형성",
        eligibility_rules={"age_min": 19, "age_max": 34},
        benefit_info={},
    )
    ineligible = Policy(
        title="부적격 정책",
        category="청년자산형성",
        eligibility_rules={"age_max": 20},
        benefit_info={},
    )
    db_session.add_all([eligible, ineligible])
    db_session.commit()

    ranked = score_and_rank(db_session, _profile(age=27), goals=[], life_events=[])

    titles_in_order = [r.title for r in ranked]
    assert titles_in_order.index("적격 정책") < titles_in_order.index("부적격 정책")


def test_life_event_relevance_boosts_matching_category(db_session):
    newlywed_policy = Policy(
        title="신혼부부 지원",
        category="신혼부부지원",
        eligibility_rules={},
        benefit_info={},
    )
    unrelated_policy = Policy(
        title="창업 지원",
        category="취업창업지원",
        eligibility_rules={},
        benefit_info={},
    )
    db_session.add_all([newlywed_policy, unrelated_policy])
    db_session.commit()

    event = SimpleNamespace(event_type="MARRIAGE")
    ranked = score_and_rank(db_session, _profile(), goals=[], life_events=[event])

    titles_in_order = [r.title for r in ranked]
    assert titles_in_order.index("신혼부부 지원") < titles_in_order.index("창업 지원")


def test_urgency_prioritizes_closer_deadline(db_session):
    urgent = Policy(
        title="마감임박 정책",
        category="지역청년지원",
        eligibility_rules={},
        benefit_info={},
        application_end=date.today() + timedelta(days=5),
    )
    distant = Policy(
        title="여유있는 정책",
        category="지역청년지원",
        eligibility_rules={},
        benefit_info={},
        application_end=date.today() + timedelta(days=200),
    )
    db_session.add_all([urgent, distant])
    db_session.commit()

    ranked = score_and_rank(db_session, _profile(), goals=[], life_events=[])

    titles_in_order = [r.title for r in ranked]
    assert titles_in_order.index("마감임박 정책") < titles_in_order.index("여유있는 정책")


def test_conflict_penalty_demotes_lower_ranked_loan(db_session):
    loan_a = Policy(
        title="대출A", category="대출", eligibility_rules={},
        benefit_info={"support_content": "최대 5000만원 지원"},
    )
    loan_b = Policy(
        title="대출B", category="대출", eligibility_rules={},
        benefit_info={"support_content": "최대 1000만원 지원"},
    )
    db_session.add_all([loan_a, loan_b])
    db_session.commit()

    ranked = score_and_rank(db_session, _profile(), goals=[], life_events=[])
    by_title = {r.title: r for r in ranked}

    assert by_title["대출A"].conflict_penalty == 0.0
    assert by_title["대출B"].conflict_penalty > 0.0
    assert by_title["대출B"].priority_score < by_title["대출A"].priority_score


def test_financial_product_uses_rate_for_benefit(db_session):
    product = FinancialProduct(
        provider="테스트은행",
        title="테스트적금",
        category="적금",
        product_rules={},
        rate_info={"max_rate": 6.0},
    )
    db_session.add(product)
    db_session.commit()

    ranked = score_and_rank(db_session, _profile(), goals=[], life_events=[])
    result = next(r for r in ranked if r.title == "테스트적금")
    assert result.score_breakdown["benefit"] == 1.0


def test_goal_relevance_keyword_similarity_none_matches_table_only():
    table_only = goal_relevance_component(["SEED_MONEY"], "청년자산형성")
    explicit_none = goal_relevance_component(["SEED_MONEY"], "청년자산형성", keyword_similarity=None)
    assert table_only == explicit_none == 1.0


def test_goal_relevance_blends_keyword_similarity_with_table():
    # SEED_MONEY x 청년자산형성 표값은 1.0. 블렌딩 비율은 0.6(표) : 0.4(유사도).
    low_similarity = goal_relevance_component(["SEED_MONEY"], "청년자산형성", keyword_similarity=0.0)
    high_similarity = goal_relevance_component(["SEED_MONEY"], "청년자산형성", keyword_similarity=1.0)

    assert low_similarity == pytest.approx(0.6)
    assert high_similarity == pytest.approx(1.0)
    assert low_similarity < high_similarity


def test_score_and_rank_accepts_keywords_without_breaking_offline(db_session):
    # 오프라인 폴백 상태에서는 keyword_similarity_scores가 빈 dict를 반환하므로, keywords를
    # 넘기든 안 넘기든 결과가 동일해야 한다(회귀 방지).
    db_session.add(
        Policy(title="자산형성 정책", category="청년자산형성", eligibility_rules={}, benefit_info={})
    )
    db_session.commit()

    profile = _profile()
    without_keywords = score_and_rank(db_session, profile, goals=[], life_events=[])
    with_keywords = score_and_rank(db_session, profile, goals=[], life_events=[], keywords=["이직 준비중"])

    assert [c.priority_score for c in without_keywords] == [c.priority_score for c in with_keywords]
