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
def setup_mock_task(mock_task_id):
    tasks[mock_task_id] = {
        "status": "complete",
        "result": [
            {
                "email_subject": "Your Coinbase purchase of 0.001 BTC",
                "vendor": "Coinbase",
                "currency": "USD",
                "amount": "100.00",
                "purchase_date": "2023-11-12",
                "transaction_id": "N/A",
                "crypto_currency": "BTC",
                "crypto_amount": "0.001",
                "confidence_score": 0.95
            }
        ]
    }
    yield

def test_upload_file_and_get_results():
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
    assert response_json["result"][0]["email_subject"] == "Your Coinbase purchase of 0.001 BTC"

def test_export_csv(mock_task_id):
    response = client.get(f"/api/export/csv/{mock_task_id}")
    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "Your Coinbase purchase of 0.001 BTC" in response.text

def test_export_json(mock_task_id):
    response = client.get(f"/api/export/json/{mock_task_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "Your Coinbase purchase of 0.001 BTC" in response.text

def test_update_record(mock_task_id):
    updated_data = {
        "vendor": "Updated Vendor",
        "amount": "200.00"
    }
    # Ensure it's pending initially
    tasks[mock_task_id]["result"][0]["review_status"] = "approved"

    response = client.put(f"/api/task/{mock_task_id}/records/0", json=updated_data)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["updated_record"]["vendor"] == "Updated Vendor"
    assert response.json()["updated_record"]["amount"] == "200.00"
    # Should be reset to pending
    assert response.json()["updated_record"]["review_status"] == "pending"

    # Verify the update is reflected in the task store
    assert tasks[mock_task_id]["result"][0]["vendor"] == "Updated Vendor"


def test_approve_record(mock_task_id):
    tasks[mock_task_id]["result"][0]["review_status"] = "pending"
    response = client.put(f"/api/task/{mock_task_id}/records/0/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["record"]["review_status"] == "approved"
    assert tasks[mock_task_id]["result"][0]["review_status"] == "approved"


def test_approve_batch(mock_task_id):
    # Add a second record
    tasks[mock_task_id]["result"].append({
        "vendor": "Test Vendor 2",
        "review_status": "pending"
    })

    tasks[mock_task_id]["result"][0]["review_status"] = "pending"
    tasks[mock_task_id]["result"][1]["review_status"] = "pending"

    response = client.post(f"/api/task/{mock_task_id}/approve-batch", json=[0, 1])
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert 0 in response.json()["approved_indices"]
    assert 1 in response.json()["approved_indices"]
    assert tasks[mock_task_id]["result"][0]["review_status"] == "approved"
    assert tasks[mock_task_id]["result"][1]["review_status"] == "approved"

def test_update_record_not_found(mock_task_id):
    response = client.put(f"/api/task/non-existent/records/0", json={})
    assert response.status_code == 404

def test_update_record_out_of_bounds(mock_task_id):
    response = client.put(f"/api/task/{mock_task_id}/records/999", json={})
    assert response.status_code == 404
