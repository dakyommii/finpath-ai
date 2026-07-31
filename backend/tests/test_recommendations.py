from models import Policy
from tests.helpers import create_user_id


def test_generate_recommendations_returns_ranked_items(client, db_session):
    db_session.add(
        Policy(
            title="청년 자산형성 정책",
            category="청년자산형성",
            eligibility_rules={"age_min": 19, "age_max": 34},
            benefit_info={},
        )
    )
    db_session.commit()

    user_id = create_user_id(client)
    client.post(
        "/api/v1/goals",
        json={"user_id": user_id, "goal_type": "SEED_MONEY"},
    )

    response = client.post("/api/v1/recommendations/generate", json={"user_id": user_id})
    assert response.status_code == 200
    items = response.json()["items"]
    assert len(items) >= 1
    assert items[0]["priority_score"] >= items[-1]["priority_score"]
    titles = [item["title"] for item in items]
    assert "청년 자산형성 정책" in titles


def test_generate_recommendations_missing_profile_returns_404(client):
    response = client.post(
        "/api/v1/recommendations/generate",
        json={"user_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 404
