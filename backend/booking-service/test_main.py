import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId
from datetime import datetime
from main import app

client = TestClient(app)

@pytest.fixture
def mock_booking():
    return {
        "_id": ObjectId(),
        "customer_id": str(ObjectId()),
        "movie_id": str(ObjectId()),
        "showtime_id": str(ObjectId()),
        "seats": ["A1", "A2"],
        "total_amount": 20.0,
        "status": "pending",
        "created_at": datetime.utcnow()
    }

@patch("main.send_sqs_message")
@patch("main.db.bookings.insert_one")
def test_create_booking(mock_insert_one, mock_send_sqs):
    # Mock database response
    mock_insert_one.return_value = AsyncMock(inserted_id=ObjectId())
    
    # Mock SQS response
    mock_send_sqs.return_value = AsyncMock(return_value={"MessageId": "test-message-id"})
    
    booking_data = {
        "customer_id": str(ObjectId()),
        "movie_id": str(ObjectId()),
        "showtime_id": str(ObjectId()),
        "seats": ["B1", "B2"],
        "total_amount": 25.0
    }
    
    response = client.post("/bookings", json=booking_data)
    
    assert response.status_code == 200
    created_booking = response.json()
    assert created_booking["customer_id"] == booking_data["customer_id"]
    assert created_booking["seats"] == booking_data["seats"]
    assert created_booking["status"] == "pending"
    assert "_id" in created_booking

@patch("main.db.bookings.find_one")
def test_get_booking(mock_find_one, mock_booking):
    mock_find_one.return_value = mock_booking
    
    booking_id = str(mock_booking["_id"])
    response = client.get(f"/bookings/{booking_id}")
    
    assert response.status_code == 200
    booking = response.json()
    assert booking["customer_id"] == mock_booking["customer_id"]
    assert booking["status"] == mock_booking["status"]
    assert booking["_id"] == booking_id

@patch("main.db.bookings.find_one")
def test_get_booking_not_found(mock_find_one):
    mock_find_one.return_value = None
    
    response = client.get(f"/bookings/{str(ObjectId())}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"

@patch("main.db.bookings.find")
def test_get_customer_bookings(mock_find, mock_booking):
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [mock_booking]
    mock_find.return_value = mock_cursor
    
    customer_id = mock_booking["customer_id"]
    response = client.get(f"/bookings/customer/{customer_id}")
    
    assert response.status_code == 200
    bookings = response.json()
    assert len(bookings) == 1
    assert bookings[0]["customer_id"] == customer_id

@patch("main.db.bookings.update_one")
def test_update_booking_status(mock_update_one):
    mock_update_one.return_value = AsyncMock(modified_count=1)
    
    booking_id = str(ObjectId())
    new_status = "confirmed"
    
    response = client.put(f"/bookings/{booking_id}/status?status={new_status}")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Booking status updated successfully"

@patch("main.db.bookings.update_one")
def test_update_booking_status_not_found(mock_update_one):
    mock_update_one.return_value = AsyncMock(modified_count=0)
    
    booking_id = str(ObjectId())
    new_status = "cancelled"
    
    response = client.put(f"/bookings/{booking_id}/status?status={new_status}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Booking not found"

@patch("main.sqs.send_message")
def test_send_sqs_message_success(mock_send_message):
    mock_send_message.return_value = {"MessageId": "test-message-id"}
    
    @pytest.mark.asyncio
    async def run_test():
        from main import send_sqs_message
        result = await send_sqs_message("test-queue-url", {"test": "message"})
        assert result["MessageId"] == "test-message-id"
    
    import asyncio
    asyncio.run(run_test()) 