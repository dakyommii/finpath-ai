from enum import Enum


class FactorStatus(str, Enum):
    MET = "MET"
    NOT_MET = "NOT_MET"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
    NOT_APPLICABLE = "NOT_APPLICABLE"


def check_age(profile, rules: dict) -> FactorStatus:
    age_min = rules.get("age_min")
    age_max = rules.get("age_max")
    if age_min is None and age_max is None:
        return FactorStatus.NOT_APPLICABLE
    if age_min is not None and profile.age < age_min:
        return FactorStatus.NOT_MET
    if age_max is not None and profile.age > age_max:
        return FactorStatus.NOT_MET
    return FactorStatus.MET


def check_income(profile, rules: dict) -> FactorStatus:
    income_max = rules.get("income_max")
    if income_max is None:
        return FactorStatus.NOT_APPLICABLE
    if profile.annual_income > income_max:
        return FactorStatus.NOT_MET
    return FactorStatus.MET


def check_region(profile, rules: dict) -> FactorStatus:
    region = rules.get("region")
    if not region:
        return FactorStatus.NOT_APPLICABLE
    return FactorStatus.MET if profile.region in region else FactorStatus.NOT_MET


def check_marital_status(profile, rules: dict) -> FactorStatus:
    marital_status = rules.get("marital_status")
    if not marital_status:
        return FactorStatus.NOT_APPLICABLE
    return FactorStatus.MET if profile.marital_status in marital_status else FactorStatus.NOT_MET


def check_homeownership(profile, rules: dict) -> FactorStatus:
    homeownership = rules.get("homeownership")
    if not homeownership:
        return FactorStatus.NOT_APPLICABLE
    # FinancialProfile has no explicit "주택 보유 여부" field (housing_type은 현재 거주형태일 뿐
    # 주택 보유 여부를 단정할 수 없음) — 임의 추정하지 않고 항상 사용자 확인이 필요하다고 표시한다.
    return FactorStatus.NEEDS_CONFIRMATION


def check_target_group(profile, rules: dict) -> FactorStatus:
    target_group = rules.get("target_group")
    if not target_group:
        return FactorStatus.NOT_APPLICABLE
    user_groups = getattr(profile, "special_status", None) or []
    return FactorStatus.MET if any(g in user_groups for g in target_group) else FactorStatus.NOT_MET


FACTOR_CHECKS = {
    "age": check_age,
    "income": check_income,
    "region": check_region,
    "marital_status": check_marital_status,
    "homeownership": check_homeownership,
    "target_group": check_target_group,
}


def evaluate_rules(profile, rules: dict) -> dict:
    rules = rules or {}
    return {name: check(profile, rules) for name, check in FACTOR_CHECKS.items()}
