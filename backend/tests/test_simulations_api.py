from models import Policy
from tests.helpers import create_user_id


def _create_roadmap(client, db_session, goal_type="HOME_PURCHASE"):
    db_session.add(
        Policy(
            title="청년내일저축계좌",
            category="청년자산형성",
            eligibility_rules={"age_min": 19, "age_max": 34},
            benefit_info={},
        )
    )
    db_session.commit()

    user_id = create_user_id(client)
    client.post("/api/v1/goals", json={"user_id": user_id, "goal_type": goal_type, "target_amount": 50000000})
    response = client.post("/api/v1/roadmaps/generate", json={"user_id": user_id})
    return response.json()["roadmap_id"]


def test_simulate_higher_saving_returns_comparison(client, db_session):
    roadmap_id = _create_roadmap(client, db_session)

    response = client.post(f"/api/v1/roadmaps/{roadmap_id}/simulate", json={"monthly_saving": 1500000})
    assert response.status_code == 200
    data = response.json()
    assert "original_estimated_completion_date" in data
    assert "simulated_estimated_completion_date" in data
    assert isinstance(data["added_steps"], list)
    assert isinstance(data["simulated_steps"], list)


def test_simulate_marriage_event_adds_step(client, db_session):
    roadmap_id = _create_roadmap(client, db_session, goal_type="JEONSE")

    response = client.post(
        f"/api/v1/roadmaps/{roadmap_id}/simulate",
        json={"life_events": [{"event_type": "MARRIAGE"}]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "신혼부부 지원 검토" in data["added_steps"]


def test_simulate_unknown_roadmap_returns_404(client):
    response = client.post(
        "/api/v1/roadmaps/00000000-0000-0000-0000-000000000000/simulate", json={}
    )
    assert response.status_code == 404
