from dataclasses import dataclass
from enum import Enum

from rules.policy_rules import FactorStatus, evaluate_rules


class EligibilityStatus(str, Enum):
    ELIGIBLE = "ELIGIBLE"
    CONDITIONAL = "CONDITIONAL"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"


@dataclass
class EligibilityResult:
    item_type: str  # "POLICY" or "FINANCIAL_PRODUCT"
    item_id: str
    title: str
    status: EligibilityStatus
    factors: dict[str, str]


def determine_status(factors: dict[str, FactorStatus]) -> EligibilityStatus:
    values = factors.values()
    if any(v == FactorStatus.NOT_MET for v in values):
        return EligibilityStatus.NOT_ELIGIBLE
    if any(v == FactorStatus.NEEDS_CONFIRMATION for v in values):
        return EligibilityStatus.CONDITIONAL
    return EligibilityStatus.ELIGIBLE


def evaluate_policy(profile, policy) -> EligibilityResult:
    factors = evaluate_rules(profile, policy.eligibility_rules)
    return EligibilityResult(
        item_type="POLICY",
        item_id=str(policy.id),
        title=policy.title,
        status=determine_status(factors),
        factors={k: v.value for k, v in factors.items()},
    )


def evaluate_financial_product(profile, product) -> EligibilityResult:
    factors = evaluate_rules(profile, product.product_rules)
    return EligibilityResult(
        item_type="FINANCIAL_PRODUCT",
        item_id=str(product.id),
        title=product.title,
        status=determine_status(factors),
        factors={k: v.value for k, v in factors.items()},
    )


def evaluate_all(db, profile) -> list[EligibilityResult]:
    from models import FinancialProduct, Policy

    results = [evaluate_policy(profile, policy) for policy in db.query(Policy).all()]
    results += [evaluate_financial_product(profile, product) for product in db.query(FinancialProduct).all()]
    return results
