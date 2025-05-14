from fastapi import APIRouter, Depends
from app.services.service_client import call_service
from app.config.settings import MOVIE_SERVICE_URL

router = APIRouter(prefix="/movies", tags=["movies"])

@router.get("/")
async def get_movies():
    """Lấy danh sách tất cả phim"""
    return await call_service(f"{MOVIE_SERVICE_URL}/movies")

@router.get("/{movie_id}")
async def get_movie(movie_id: str):
    """Lấy thông tin chi tiết một phim"""
    return await call_service(f"{MOVIE_SERVICE_URL}/movies/{movie_id}")

@router.get("/{movie_id}/showtimes")
async def get_movie_showtimes(movie_id: str):
    """Lấy danh sách suất chiếu của một phim"""
    return await call_service(f"{MOVIE_SERVICE_URL}/showtimes/movie/{movie_id}") 