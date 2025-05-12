import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from bson import ObjectId
from datetime import datetime
from main import app

client = TestClient(app)

@pytest.fixture
def mock_movie():
    return {
        "_id": ObjectId(),
        "title": "Test Movie",
        "description": "Test description",
        "duration": 120,
        "genre": "Action",
        "director": "Test Director",
        "cast": ["Actor 1", "Actor 2"],
        "release_date": datetime.now().isoformat(),
        "poster_url": "http://example.com/poster.jpg",
        "trailer_url": "http://example.com/trailer.mp4",
        "rating": 8.5,
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture
def mock_showtime():
    return {
        "_id": ObjectId(),
        "movie_id": str(ObjectId()),
        "time": datetime.now().isoformat(),
        "theater": "Theater 1",
        "price": 10.5,
        "created_at": datetime.now().isoformat()
    }

@patch("main.db.movies.find")
def test_get_movies(mock_find, mock_movie):
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [mock_movie]
    mock_find.return_value = mock_cursor
    
    response = client.get("/movies")
    
    assert response.status_code == 200
    movies = response.json()
    assert len(movies) == 1
    assert movies[0]["title"] == mock_movie["title"]
    assert "id" in movies[0]
    assert "_id" not in movies[0]

@patch("main.db.movies.find_one")
def test_get_movie(mock_find_one, mock_movie):
    mock_find_one.return_value = mock_movie
    
    movie_id = str(mock_movie["_id"])
    response = client.get(f"/movies/{movie_id}")
    
    assert response.status_code == 200
    movie = response.json()
    assert movie["title"] == mock_movie["title"]
    assert movie["id"] == movie_id
    assert "_id" not in movie

@patch("main.db.movies.find_one")
def test_get_movie_not_found(mock_find_one):
    mock_find_one.return_value = None
    
    response = client.get(f"/movies/{str(ObjectId())}")
    
    assert response.status_code == 404
    assert response.json()["detail"] == "Movie not found"

@patch("main.db.movies.insert_one")
def test_create_movie(mock_insert_one):
    mock_insert_one.return_value = AsyncMock(inserted_id=ObjectId())
    
    movie_data = {
        "title": "New Movie",
        "description": "New description",
        "duration": 90,
        "genre": "Comedy",
        "director": "New Director",
        "cast": ["Actor 3", "Actor 4"],
        "release_date": datetime.now().isoformat(),
        "poster_url": "http://example.com/new-poster.jpg",
        "trailer_url": "http://example.com/new-trailer.mp4",
        "rating": 7.5
    }
    
    response = client.post("/movies", json=movie_data)
    
    assert response.status_code == 200
    created_movie = response.json()
    assert created_movie["title"] == movie_data["title"]
    assert "id" in created_movie

@patch("main.db.showtimes.find")
def test_get_movie_showtimes(mock_find, mock_showtime):
    mock_cursor = AsyncMock()
    mock_cursor.to_list.return_value = [mock_showtime]
    mock_find.return_value = mock_cursor
    
    movie_id = mock_showtime["movie_id"]
    response = client.get(f"/showtimes/movie/{movie_id}")
    
    assert response.status_code == 200
    showtimes = response.json()
    assert len(showtimes) == 1
    assert showtimes[0]["movie_id"] == movie_id 