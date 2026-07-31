"""24장 데모 시나리오 재현 (24.4 AI 상담은 Phase 10 보류로 제외).

24.1 입력값 -> 24.2/24.3 진단·로드맵 -> 24.5 시뮬레이션까지 API 엔드투엔드로 검증한다.
"""

from models import FinancialProduct, Policy

DEMO_PROFILE_PAYLOAD = {
    "age": 27,
    "region": "서울",
    "job_status": "EMPLOYED",
    "annual_income": 38000000,
    "marital_status": "SINGLE",
    "housing_type": "MONTHLY_RENT",
    "liquid_assets": 20000000,
    "total_debt": 0,
    "monthly_saving": 1000000,
}


def _seed_demo_candidates(db_session):
    db_session.add_all(
        [
            Policy(
                title="청년내일저축계좌", category="청년자산형성",
                eligibility_rules={"age_min": 19, "age_max": 34, "income_max": 26000000},
                benefit_info={"support_content": "정부 매칭 지원"},
            ),
            Policy(
                title="청년내일채움공제", category="청년자산형성",
                eligibility_rules={"age_min": 15, "age_max": 34}, benefit_info={},
            ),
            FinancialProduct(
                provider="테스트은행", title="테스트 청년적금", category="적금",
                product_rules={}, rate_info={"max_rate": 4.5},
            ),
            Policy(
                title="청년전용 버팀목전세자금대출", category="대출",
                eligibility_rules={}, benefit_info={},
            ),
            FinancialProduct(
                provider="테스트증권", title="테스트 ISA", category="ISA", product_rules={},
            ),
            Policy(
                title="디딤돌대출(생애최초 주택구입)", category="대출",
                eligibility_rules={}, benefit_info={},
            ),
        ]
    )
    db_session.commit()


def test_demo_scenario_produces_diagnosis_and_roadmap(client, db_session):
    _seed_demo_candidates(db_session)

    profile_resp = client.post("/api/v1/profiles", json=DEMO_PROFILE_PAYLOAD)
    assert profile_resp.status_code == 201
    user_id = profile_resp.json()["user_id"]

    goal_resp = client.post(
        "/api/v1/goals",
        json={"user_id": user_id, "goal_type": "HOME_PURCHASE", "target_amount": 100000000, "target_date": "2032-12-31"},
    )
    assert goal_resp.status_code == 201
    client.post("/api/v1/goals", json={"user_id": user_id, "goal_type": "JEONSE"})

    recs = client.post("/api/v1/recommendations/generate", json={"user_id": user_id})
    assert recs.status_code == 200
    assert len(recs.json()["items"]) > 0

    roadmap_resp = client.post("/api/v1/roadmaps/generate", json={"user_id": user_id})
    assert roadmap_resp.status_code == 201
    roadmap = roadmap_resp.json()

    # 24.3 예시와 동일한 구조: 비상자금 -> 자산형성 -> ... -> 주택구입 순서
    titles = [s["title"] for s in roadmap["steps"]]
    assert titles[0] == "비상자금 확보"
    assert "주택 구입 준비" in titles
    assert titles.index("전세자금 마련 준비") < titles.index("주택 구입 준비")

    get_resp = client.get(f"/api/v1/roadmaps/{roadmap['roadmap_id']}")
    assert get_resp.status_code == 200
    assert get_resp.json()["steps"] == roadmap["steps"]


def test_demo_scenario_simulation_matches_24_5(client, db_session):
    _seed_demo_candidates(db_session)

    profile_resp = client.post("/api/v1/profiles", json=DEMO_PROFILE_PAYLOAD)
    user_id = profile_resp.json()["user_id"]
    client.post(
        "/api/v1/goals",
        json={"user_id": user_id, "goal_type": "HOME_PURCHASE", "target_amount": 100000000},
    )
    roadmap = client.post("/api/v1/roadmaps/generate", json={"user_id": user_id}).json()

    # 24.5: 월 저축액 100만원 -> 120만원, 내년 결혼 예정
    sim_resp = client.post(
        f"/api/v1/roadmaps/{roadmap['roadmap_id']}/simulate",
        json={"monthly_saving": 1200000, "life_events": [{"event_type": "MARRIAGE"}]},
    )
    assert sim_resp.status_code == 200
    sim = sim_resp.json()

    assert "신혼부부 지원 검토" in sim["added_steps"]
    assert sim["removed_steps"] == []
