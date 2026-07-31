import json
from datetime import date, datetime
from pathlib import Path

from core.db import SessionLocal
from models import FinancialProduct, Policy

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _parse_date(value):
    return date.fromisoformat(value) if value else None


def _parse_datetime(value):
    return datetime.fromisoformat(value) if value else None


def seed_policies(db):
    with open(DATA_DIR / "policies.json", encoding="utf-8") as f:
        payload = json.load(f)
    items = payload["items"]
    created = 0
    for item in items:
        exists = db.query(Policy).filter(Policy.title == item["title"]).first()
        if exists:
            continue
        db.add(
            Policy(
                title=item["title"],
                category=item["category"],
                description=item.get("description"),
                eligibility_rules=item["eligibility_rules"],
                benefit_info=item.get("benefit_info"),
                application_start=_parse_date(item.get("application_start")),
                application_end=_parse_date(item.get("application_end")),
                official_url=item.get("official_url"),
                last_verified_at=_parse_datetime(item.get("last_verified_at")),
            )
        )
        created += 1
    db.commit()
    return created, len(items)


def seed_financial_products(db):
    with open(DATA_DIR / "financial_products.json", encoding="utf-8") as f:
        payload = json.load(f)
    items = payload["items"]
    created = 0
    for item in items:
        exists = (
            db.query(FinancialProduct)
            .filter(
                FinancialProduct.provider == item["provider"],
                FinancialProduct.title == item["title"],
            )
            .first()
        )
        if exists:
            continue
        db.add(
            FinancialProduct(
                provider=item["provider"],
                title=item["title"],
                category=item["category"],
                product_rules=item["product_rules"],
                rate_info=item.get("rate_info"),
                benefit_info=item.get("benefit_info"),
                official_url=item.get("official_url"),
                last_verified_at=_parse_datetime(item.get("last_verified_at")),
            )
        )
        created += 1
    db.commit()
    return created, len(items)


def main():
    db = SessionLocal()
    try:
        p_created, p_total = seed_policies(db)
        f_created, f_total = seed_financial_products(db)
        print(f"policies: {p_created} inserted / {p_total} in file")
        print(f"financial_products: {f_created} inserted / {f_total} in file")
    finally:
        db.close()


if __name__ == "__main__":
    main()
