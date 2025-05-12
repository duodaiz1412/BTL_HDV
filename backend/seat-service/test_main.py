import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from bson import ObjectId
from datetime import datetime
from main import app

client = TestClient(app)

@pytest.fixture
def mock_seat():
    return {
        "_id": ObjectId(),
        "showtime_id": str(ObjectId()),
        "seat_number": "A1",
        "status": "available",
        "created_at": datetime.utcnow().isoformat()
    }

@pytest.fixture
def mock_seats():
    return [
        {
            "_id": ObjectId(),
            "showtime_id": str(ObjectId()),
            "seat_number": "A1",
            "status": "available",
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "_id": ObjectId(),
            "showtime_id": str(ObjectId()),
            "seat_number": "A2",
            "status": "available",
            "created_at": datetime.utcnow().isoformat()
        }
    ]

@patch("main.db.seats.insert_one")
def test_create_seat(mock_insert_one):
    mock_insert_one.return_value = AsyncMock(inserted_id=ObjectId())
    
    seat_data = {
        "showtime_id": str(ObjectId()),
        "seat_number": "B1",
        "status": "available"
    }
    
    response = client.post("/seats", json=seat_data)
    
    assert response.status_code == 200
    created_seat = response.json()
    assert created_seat["showtime_id"] == seat_data["showtime_id"]
    assert created_seat["seat_number"] == seat_data["seat_number"]
    assert created_seat["status"] == "available"
    assert "id" in created_seat

@patch("main.db.seats.find_one")
def test_get_seat(mock_find_one, mock_seat):
    mock_find_one.return_value = mock_seat
    
    seat_id = str(mock_seat["_id"])
    response = client.get(f"/seats/{seat_id}")
    
    assert response.status_code == 200
    seat = response.json()
    assert seat["showtime_id"] == mock_seat["showtime_id"]
    assert seat["seat_number"] == mock_seat["seat_number"]
    assert seat["_id"] == seat_id

@patch("main.db.seats.find_one")
def test_get_seat_not_found(mock_find_one):
    mock_find_one.return_value = None
    
    response = client.get(f"/seats/{str(ObjectId())}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Seat not found"

@patch("main.db.seats.find")
def test_get_showtime_seats(mock_find, mock_seats):
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = mock_seats
    mock_find.return_value = mock_cursor
    
    showtime_id = mock_seats[0]["showtime_id"]
    response = client.get(f"/seats/showtime/{showtime_id}")
    
    assert response.status_code == 200
    seats = response.json()
    assert len(seats) == 2
    assert seats[0]["showtime_id"] == showtime_id
    assert seats[1]["showtime_id"] == showtime_id

@patch("main.db.seats.update_one")
def test_update_seat_status(mock_update_one):
    mock_update_one.return_value = AsyncMock(modified_count=1)
    
    seat_id = str(ObjectId())
    new_status = "booked"
    
    response = client.put(f"/seats/{seat_id}/status?status={new_status}")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Seat status updated successfully"

@patch("main.db.seats.update_one")
def test_update_seat_status_not_found(mock_update_one):
    mock_update_one.return_value = AsyncMock(modified_count=0)
    
    seat_id = str(ObjectId())
    new_status = "booked"
    
    response = client.put(f"/seats/{seat_id}/status?status={new_status}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Seat not found"

@patch("main.db.seats.find_one")
def test_check_seats_success(mock_find_one):
    mock_find_one.return_value = {"_id": ObjectId(), "status": "available"}
    
    showtime_id = str(ObjectId())
    seat_numbers = ["A1", "A2"]
    
    response = client.post(f"/seats/check?showtime_id={showtime_id}", json=seat_numbers)
    
    assert response.status_code == 200
    assert response.json()["message"] == "All seats are available"

@patch("main.db.seats.find_one")
def test_check_seats_unavailable(mock_find_one):
    # First seat is available, second is not
    mock_find_one.side_effect = [
        {"_id": ObjectId(), "status": "available"},
        None
    ]
    
    showtime_id = str(ObjectId())
    seat_numbers = ["A1", "A2"]
    
    response = client.post(f"/seats/check?showtime_id={showtime_id}", json=seat_numbers)
    
    assert response.status_code == 400
    assert "not available" in response.json()["detail"]

@patch("main.send_sqs_message")
@patch("main.db.seats.update_many")
@patch("main.check_seats")
def test_book_seats_success(mock_check, mock_update, mock_sqs):
    mock_check.return_value = {"message": "All seats are available"}
    mock_update.return_value = AsyncMock(modified_count=2)
    mock_sqs.return_value = {"MessageId": "test-id"}
    
    showtime_id = str(ObjectId())
    seat_numbers = ["A1", "A2"]
    
    response = client.post(f"/seats/book?showtime_id={showtime_id}", json=seat_numbers)
    
    assert response.status_code == 200
    assert response.json()["message"] == "Seats booked successfully" 