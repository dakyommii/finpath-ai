from tests.helpers import create_user_id


def test_create_interest_keywords_success(client):
    user_id = create_user_id(client)
    response = client.post(
        "/api/v1/interest-keywords",
        json={
            "user_id": user_id,
            "keywords": [
                {"axis": "CAREER", "keyword": "이직 준비중"},
                {"axis": "FAMILY_PLAN", "keyword": "곧 결혼 예정"},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 2
    assert {item["keyword"] for item in data} == {"이직 준비중", "곧 결혼 예정"}
    assert all(item["user_id"] == user_id for item in data)


def test_create_interest_keywords_unknown_user_returns_404(client):
    response = client.post(
        "/api/v1/interest-keywords",
        json={
            "user_id": "00000000-0000-0000-0000-000000000000",
            "keywords": [{"axis": "CAREER", "keyword": "이직 준비중"}],
        },
    )
    assert response.status_code == 404


def test_create_interest_keywords_empty_list_rejected(client):
    user_id = create_user_id(client)
    response = client.post(
        "/api/v1/interest-keywords", json={"user_id": user_id, "keywords": []}
    )
    assert response.status_code == 422
