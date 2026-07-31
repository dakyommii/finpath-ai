from types import SimpleNamespace

from models import FinancialProduct, Policy
from services.eligibility_service import EligibilityStatus, evaluate_all


def test_evaluate_all_batches_policies_and_products(db_session):
    eligible_policy = Policy(
        title="테스트 청년정책",
        category="테스트",
        eligibility_rules={"age_min": 19, "age_max": 34},
        benefit_info={},
    )
    ineligible_policy = Policy(
        title="테스트 소득제한정책",
        category="테스트",
        eligibility_rules={"income_max": 10000000},
        benefit_info={},
    )
    product = FinancialProduct(
        provider="테스트은행",
        title="테스트적금",
        category="적금",
        product_rules={"age_min": 19, "age_max": 34},
    )
    db_session.add_all([eligible_policy, ineligible_policy, product])
    db_session.commit()

    profile = SimpleNamespace(age=27, annual_income=38000000, region="서울", marital_status="SINGLE")
    results = evaluate_all(db_session, profile)

    assert len(results) == 3
    by_title = {r.title: r for r in results}
    assert by_title["테스트 청년정책"].status == EligibilityStatus.ELIGIBLE
    assert by_title["테스트 소득제한정책"].status == EligibilityStatus.NOT_ELIGIBLE
    assert by_title["테스트적금"].item_type == "FINANCIAL_PRODUCT"
    assert by_title["테스트적금"].status == EligibilityStatus.ELIGIBLE
