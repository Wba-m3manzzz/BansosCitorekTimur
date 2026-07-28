from fastapi.testclient import TestClient
from unittest.mock import MagicMock

from app.main import app
from app.services.gemini_service import gemini_service


def test_chat_returns_friendly_error_when_gemini_is_not_configured(monkeypatch):
    monkeypatch.setattr("app.services.gemini_service.settings.GEMINI_API_KEY", "")
    client = TestClient(app)

    response = client.post(
        "/api/chat",
        json={"message": "Bagaimana cara menggunakan website?", "conversation_id": "test-conversation"},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Maaf, chatbot sedang mengalami gangguan. Silakan coba beberapa saat lagi."


def test_chat_delegates_to_gemini_with_enriched_context(monkeypatch):
    monkeypatch.setattr("app.services.gemini_service.settings.GEMINI_API_KEY", "test-key")
    
    # Mock DB lookup
    monkeypatch.setattr(
        gemini_service,
        "_lookup_warga_by_nik",
        lambda nik: {"nik": "3602010101010001", "nama": "Ahmad", "status_prediksi": "Layak"}
        if nik == "3602010101010001"
        else None,
    )

    # Mock Gemini client
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Halo Ahmad, status kelayakan Anda adalah Layak."
    mock_client.models.generate_content.return_value = mock_response

    monkeypatch.setattr(gemini_service, "_get_client", lambda: mock_client)

    client = TestClient(app)
    response = client.post(
        "/api/chat",
        json={"message": "Cek status 3602010101010001", "conversation_id": "test-nlp-conv"},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Halo Ahmad, status kelayakan Anda adalah Layak."
    
    # Verify Gemini generate_content was called and system prompt was used
    mock_client.models.generate_content.assert_called_once()
    call_args = mock_client.models.generate_content.call_args
    sent_content = call_args.kwargs["contents"][-1].parts[0].text
    assert "[SISTEM CONTEXT DB: Ditemukan data warga NIK 3602010101010001, Nama: Ahmad, Status Kelayakan: Layak]" in sent_content
