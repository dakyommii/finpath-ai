from tests.helpers import DEFAULT_PROFILE_PAYLOAD


def test_create_profile_success(client):
    response = client.post("/api/v1/profiles", json=DEFAULT_PROFILE_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["age"] == 27
    assert data["region"] == "서울"
    assert "id" in data
    assert "user_id" in data


def test_create_profile_missing_required_field(client):
    payload = dict(DEFAULT_PROFILE_PAYLOAD)
    del payload["job_status"]
    response = client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 422


def test_create_profile_invalid_age(client):
    payload = dict(DEFAULT_PROFILE_PAYLOAD)
    payload["age"] = -1
    response = client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 422


def test_create_profile_negative_income(client):
    payload = dict(DEFAULT_PROFILE_PAYLOAD)
    payload["annual_income"] = -100
    response = client.post("/api/v1/profiles", json=payload)
    assert response.status_code == 422
