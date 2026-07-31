from tests.helpers import create_user_id


def test_create_goal_success(client):
    user_id = create_user_id(client)
    payload = {
        "user_id": user_id,
        "goal_type": "HOME_PURCHASE",
        "target_amount": 100000000,
        "target_date": "2032-12-31",
    }
    response = client.post("/api/v1/goals", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["goal_type"] == "HOME_PURCHASE"
    assert data["user_id"] == user_id


def test_create_goal_missing_required_field(client):
    payload = {"user_id": create_user_id(client)}
    response = client.post("/api/v1/goals", json=payload)
    assert response.status_code == 422


def test_create_goal_unknown_user(client):
    payload = {"user_id": "00000000-0000-0000-0000-000000000000", "goal_type": "HOME_PURCHASE"}
    response = client.post("/api/v1/goals", json=payload)
    assert response.status_code == 404
