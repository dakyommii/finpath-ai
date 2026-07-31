from tests.helpers import create_user_id


def test_create_life_event_success(client):
    user_id = create_user_id(client)
    payload = {
        "user_id": user_id,
        "event_type": "MARRIAGE",
        "expected_date": "2027-10-01",
        "certainty": "예상",
    }
    response = client.post("/api/v1/life-events", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["event_type"] == "MARRIAGE"
    assert data["user_id"] == user_id


def test_create_life_event_missing_required_field(client):
    payload = {"user_id": create_user_id(client)}
    response = client.post("/api/v1/life-events", json=payload)
    assert response.status_code == 422


def test_create_life_event_unknown_user(client):
    payload = {"user_id": "00000000-0000-0000-0000-000000000000", "event_type": "MARRIAGE"}
    response = client.post("/api/v1/life-events", json=payload)
    assert response.status_code == 404
