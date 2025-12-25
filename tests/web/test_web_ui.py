import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from io import BytesIO
from digital_asset_harvester.web.main import app
from digital_asset_harvester.web import api as web_api

@pytest.fixture
def client():
    return TestClient(app)

def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "<h1>Upload your mbox file</h1>" in response.text

@patch("digital_asset_harvester.web.api.process_mbox_file")
def test_upload_file(mock_process_mbox_file, client):
    mbox_content = b"From MAILER-DAEMON Fri Jul  5 12:54:36 2024\nContent-Type: text/plain\n\nTest email"

    response = client.post(
        "/api/upload",
        files={"file": ("test.mbox", BytesIO(mbox_content), "application/octet-stream")},
        follow_redirects=False
    )

    assert response.status_code == 303
    assert response.headers["location"].startswith("/status/")
    assert mock_process_mbox_file.called

def test_get_status(client):
    task_id = "test_task"
    web_api.tasks[task_id] = {"status": "processing", "result": None}
    response = client.get(f"/api/status/{task_id}")
    assert response.status_code == 200
    assert response.json() == {"status": "processing", "result": None}

def test_results_page(client):
    task_id = "test_task"
    web_api.tasks[task_id] = {"status": "complete", "result": [{"email_subject": "Test Subject", "vendor": "Test Vendor"}]}
    response = client.get(f"/results/{task_id}")
    assert response.status_code == 200
    assert "Test Subject" in response.text
    assert "Test Vendor" in response.text

def test_export_csv(client):
    task_id = "test_task"
    web_api.tasks[task_id] = {"status": "complete", "result": [{"email_subject": "Test Subject", "vendor": "Test Vendor"}]}
    response = client.get(f"/api/export/csv/{task_id}")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Test Subject,Test Vendor" in response.text

def test_export_csv_empty(client):
    task_id = "test_task_empty"
    web_api.tasks[task_id] = {"status": "complete", "result": []}
    response = client.get(f"/api/export/csv/{task_id}")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    expected_headers = ",".join(web_api.DEFAULT_CSV_HEADERS)
    assert expected_headers in response.text

def test_export_json(client):
    task_id = "test_task"
    web_api.tasks[task_id] = {"status": "complete", "result": [{"email_subject": "Test Subject", "vendor": "Test Vendor"}]}
    response = client.get(f"/api/export/json/{task_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == [{"email_subject": "Test Subject", "vendor": "Test Vendor"}]

def test_export_json_empty(client):
    task_id = "test_task_empty"
    web_api.tasks[task_id] = {"status": "complete", "result": []}
    response = client.get(f"/api/export/json/{task_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert response.json() == []
