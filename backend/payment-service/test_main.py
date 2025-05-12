import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId
from datetime import datetime
from main import app

client = TestClient(app)

@pytest.fixture
def mock_payment():
    return {
        "_id": ObjectId(),
        "booking_id": str(ObjectId()),
        "amount": 25.0,
        "payment_method": "credit_card",
        "status": "pending",
        "created_at": datetime.utcnow()
    }

@patch("main.send_sqs_message")
@patch("main.db.payments.insert_one")
def test_create_payment(mock_insert_one, mock_send_sqs):
    # Mock database response
    mock_insert_one.return_value = AsyncMock(inserted_id=ObjectId())
    
    # Mock SQS response
    mock_send_sqs.return_value = AsyncMock(return_value={"MessageId": "test-message-id"})
    
    payment_data = {
        "booking_id": str(ObjectId()),
        "amount": 30.0,
        "payment_method": "paypal",
        "status": "pending"
    }
    
    response = client.post("/payments", json=payment_data)
    
    assert response.status_code == 200
    created_payment = response.json()
    assert created_payment["booking_id"] == payment_data["booking_id"]
    assert created_payment["amount"] == payment_data["amount"]
    assert created_payment["payment_method"] == payment_data["payment_method"]
    assert created_payment["status"] == "pending"
    assert "_id" in created_payment

@patch("main.db.payments.find_one")
def test_get_payment(mock_find_one, mock_payment):
    mock_find_one.return_value = mock_payment
    
    payment_id = str(mock_payment["_id"])
    response = client.get(f"/payments/{payment_id}")
    
    assert response.status_code == 200
    payment = response.json()
    assert payment["booking_id"] == mock_payment["booking_id"]
    assert payment["amount"] == mock_payment["amount"]
    assert payment["payment_method"] == mock_payment["payment_method"]
    assert payment["status"] == mock_payment["status"]
    assert payment["_id"] == payment_id

@patch("main.db.payments.find_one")
def test_get_payment_not_found(mock_find_one):
    mock_find_one.return_value = None
    
    response = client.get(f"/payments/{str(ObjectId())}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"

@patch("main.db.payments.find")
def test_get_booking_payments(mock_find, mock_payment):
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [mock_payment]
    mock_find.return_value = mock_cursor
    
    booking_id = mock_payment["booking_id"]
    response = client.get(f"/payments/booking/{booking_id}")
    
    assert response.status_code == 200
    payments = response.json()
    assert len(payments) == 1
    assert payments[0]["booking_id"] == booking_id

@patch("main.db.payments.update_one")
def test_update_payment_status(mock_update_one):
    mock_update_one.return_value = AsyncMock(modified_count=1)
    
    payment_id = str(ObjectId())
    new_status = "completed"
    
    response = client.put(f"/payments/{payment_id}/status?status={new_status}")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Payment status updated successfully"

@patch("main.db.payments.update_one")
def test_update_payment_status_not_found(mock_update_one):
    mock_update_one.return_value = AsyncMock(modified_count=0)
    
    payment_id = str(ObjectId())
    new_status = "failed"
    
    response = client.put(f"/payments/{payment_id}/status?status={new_status}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found"

@patch("main.send_sqs_message")
@patch("main.db.payments.update_one")
@patch("main.db.payments.find_one")
def test_refund_payment(mock_find_one, mock_update_one, mock_send_sqs):
    payment_id = str(ObjectId())
    booking_id = str(ObjectId())
    
    # Mock payment data
    mock_find_one.return_value = {
        "_id": payment_id,
        "booking_id": booking_id,
        "amount": 50.0,
        "payment_method": "credit_card",
        "status": "completed",
        "created_at": datetime.utcnow()
    }
    
    # Mock update response
    mock_update_one.return_value = AsyncMock(modified_count=1)
    
    # Mock SQS response
    mock_send_sqs.return_value = {"MessageId": "test-message-id"}
    
    response = client.post(f"/payments/{payment_id}/refund")
    
    assert response.status_code == 200
    assert "refund_id" in response.json()
    assert response.json()["message"] == "Payment refunded successfully"

@patch("main.db.payments.find_one")
def test_refund_payment_not_found(mock_find_one):
    mock_find_one.return_value = None
    
    payment_id = str(ObjectId())
    response = client.post(f"/payments/{payment_id}/refund")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Payment not found" 