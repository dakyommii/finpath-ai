DEFAULT_PROFILE_PAYLOAD = {
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


def create_user_id(client, payload=None):
    response = client.post("/api/v1/profiles", json=payload or DEFAULT_PROFILE_PAYLOAD)
    assert response.status_code == 201
    return response.json()["user_id"]
