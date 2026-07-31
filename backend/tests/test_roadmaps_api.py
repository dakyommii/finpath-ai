from models import Policy
from tests.helpers import create_user_id


def test_generate_and_get_roadmap(client, db_session):
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
    client.post(
        "/api/v1/goals",
        json={"user_id": user_id, "goal_type": "SEED_MONEY", "target_amount": 50000000},
    )

    response = client.post("/api/v1/roadmaps/generate", json={"user_id": user_id})
    assert response.status_code == 201
    data = response.json()
    assert data["goal"]["type"] == "SEED_MONEY"
    assert len(data["steps"]) >= 1
    assert data["steps"][0]["title"] == "비상자금 확보"

    roadmap_id = data["roadmap_id"]
    get_response = client.get(f"/api/v1/roadmaps/{roadmap_id}")
    assert get_response.status_code == 200
    assert get_response.json()["roadmap_id"] == roadmap_id


def test_generate_roadmap_missing_profile_returns_404(client):
    response = client.post(
        "/api/v1/roadmaps/generate",
        json={"user_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404


def test_get_unknown_roadmap_returns_404(client):
    response = client.get("/api/v1/roadmaps/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
