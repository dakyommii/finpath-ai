from tests.helpers import create_user_id


def test_malformed_roadmap_id_returns_422(client):
    response = client.get("/api/v1/roadmaps/not-a-uuid")
    assert response.status_code == 422


def test_simulate_malformed_roadmap_id_returns_422(client):
    response = client.post("/api/v1/roadmaps/not-a-uuid/simulate", json={})
    assert response.status_code == 422


def test_simulate_negative_monthly_saving_rejected(client, db_session):
    from models import Policy

    db_session.add(Policy(title="테스트정책", category="청년자산형성", eligibility_rules={}, benefit_info={}))
    db_session.commit()

    user_id = create_user_id(client)
    client.post("/api/v1/goals", json={"user_id": user_id, "goal_type": "SEED_MONEY"})
    roadmap_id = client.post("/api/v1/roadmaps/generate", json={"user_id": user_id}).json()["roadmap_id"]

    response = client.post(f"/api/v1/roadmaps/{roadmap_id}/simulate", json={"monthly_saving": -100})
    assert response.status_code == 422


def test_simulate_negative_annual_income_rejected(client, db_session):
    from models import Policy

    db_session.add(Policy(title="테스트정책", category="청년자산형성", eligibility_rules={}, benefit_info={}))
    db_session.commit()

    user_id = create_user_id(client)
    client.post("/api/v1/goals", json={"user_id": user_id, "goal_type": "SEED_MONEY"})
    roadmap_id = client.post("/api/v1/roadmaps/generate", json={"user_id": user_id}).json()["roadmap_id"]

    response = client.post(f"/api/v1/roadmaps/{roadmap_id}/simulate", json={"annual_income": -1})
    assert response.status_code == 422


def test_roadmap_generate_with_no_goals_and_empty_catalog_does_not_crash(client):
    """정책/상품 DB가 비어 있고 목표도 없는 최소 상태에서도 500 없이 응답해야 한다."""
    user_id = create_user_id(client)
    response = client.post("/api/v1/roadmaps/generate", json={"user_id": user_id})
    assert response.status_code == 201
    data = response.json()
    assert data["steps"][0]["title"] == "비상자금 확보"
    for step in data["steps"]:
        assert step["related_items"] in (None, [])


def test_recommendations_with_empty_catalog_returns_empty_list(client):
    user_id = create_user_id(client)
    response = client.post("/api/v1/recommendations/generate", json={"user_id": user_id})
    assert response.status_code == 200
    assert response.json()["items"] == []


def test_simulate_unknown_life_event_type_ignored_gracefully(client, db_session):
    from models import Policy

    db_session.add(Policy(title="테스트정책", category="청년자산형성", eligibility_rules={}, benefit_info={}))
    db_session.commit()

    user_id = create_user_id(client)
    client.post("/api/v1/goals", json={"user_id": user_id, "goal_type": "SEED_MONEY"})
    roadmap_id = client.post("/api/v1/roadmaps/generate", json={"user_id": user_id}).json()["roadmap_id"]

    response = client.post(
        f"/api/v1/roadmaps/{roadmap_id}/simulate",
        json={"life_events": [{"event_type": "UNKNOWN_EVENT_TYPE"}]},
    )
    assert response.status_code == 200
