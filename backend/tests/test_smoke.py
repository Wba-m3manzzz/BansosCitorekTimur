from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_payload():
    client = TestClient(app)
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert "status" in payload
    assert "database" in payload
    assert "model" in payload


def test_dashboard_endpoint_returns_camelcase():
    client = TestClient(app)
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert "totalWarga" in payload["summary"]
    assert "layak" in payload["summary"]
    assert "statusDistribution" in payload
    assert "pendapatanDistribution" in payload


def test_predict_endpoint_conforms_to_contract():
    client = TestClient(app)
    payload = {
        "nik": "3202110908879999",
        "nama": "Warga Percobaan",
        "pendapatan": 750000,
        "tanggungan": 2,
        "kondisiRumah": "Tidak Layak",
        "pekerjaan": "Tani",
        "pendidikan": "SD"
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    res_data = response.json()
    assert "status" in res_data
    assert "keterangan" in res_data
    assert res_data["status"] in {"Layak", "Tidak Layak"}
