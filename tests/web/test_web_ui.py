import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from digital_asset_harvester.web.main import app
from digital_asset_harvester.web.api import tasks

client = TestClient(app)

@pytest.fixture(scope="session")
def mock_task_id():
    return "test-task-id"

@pytest.fixture(scope="session", autouse=True)
def mock_process_mbox(mock_task_id):
    tasks[mock_task_id] = {
        "status": "complete",
        "result": [
            {
                "email_subject": "Test Subject",
                "vendor": "Test Vendor",
                "currency": "USD",
                "amount": "100.00",
                "purchase_date": "2024-01-01",
                "transaction_id": "12345",
                "crypto_currency": "BTC",
                "crypto_amount": "0.002",
                "confidence_score": "0.95"
            }
        ]
    }
    with patch('digital_asset_harvester.web.api.process_mbox_file', new_callable=MagicMock) as mock:
        yield mock

def test_upload_file_and_get_results(mock_process_mbox):
    # Mock the background task
    def mock_task(task_id, temp_path, logger_factory):
        tasks[task_id] = {
            "status": "complete",
            "result": [
                {
                    "email_subject": "Test Subject",
                    "vendor": "Test Vendor",
                    "currency": "USD",
                    "amount": "100.00",
                    "purchase_date": "2024-01-01",
                    "transaction_id": "12345",
                    "crypto_currency": "BTC",
                    "crypto_amount": "0.002",
                    "confidence_score": "0.95"
                }
            ]
        }
    mock_process_mbox.side_effect = mock_task

    # 1. Upload a dummy file
    test_mbox_path = "tests/fixtures/test.mbox"
    with open(test_mbox_path, "w") as f:
        f.write("dummy content")

    with open(test_mbox_path, "rb") as f:
        response = client.post("/api/upload", files={"file": ("test.mbox", f, "application/octet-stream")})

    assert response.history[0].status_code == 303
    task_id = response.url.path.split("/")[-1]

    # 2. Poll the status endpoint and verify the data
    response = client.get(f"/api/status/{task_id}")
    assert response.status_code == 200

    response_json = response.json()
    assert response_json["status"] == "complete"
    assert response_json["result"][0]["email_subject"] == "Test Subject"

def test_export_csv(mock_task_id):
    response = client.get(f"/api/export/csv/{mock_task_id}")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Test Subject" in response.text

def test_export_json(mock_task_id):
    response = client.get(f"/api/export/json/{mock_task_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "Test Subject" in response.text

def test_update_record(mock_task_id):
    updated_data = {
        "vendor": "Updated Vendor",
        "amount": "200.00"
    }
    response = client.put(f"/api/task/{mock_task_id}/records/0", json=updated_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["updated_record"]["vendor"] == "Updated Vendor"
    assert response.json()["updated_record"]["amount"] == "200.00"

    # Verify the update is reflected in the task store
    assert tasks[mock_task_id]["result"][0]["vendor"] == "Updated Vendor"

def test_update_record_not_found(mock_task_id):
    response = client.put(f"/api/task/non-existent/records/0", json={})
    assert response.status_code == 404

def test_update_record_out_of_bounds(mock_task_id):
    response = client.put(f"/api/task/{mock_task_id}/records/999", json={})
    assert response.status_code == 404
