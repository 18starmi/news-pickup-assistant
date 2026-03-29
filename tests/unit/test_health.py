from tests.conftest import create_test_client


def test_health_endpoint_returns_ok() -> None:
    client = create_test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
