"""
Router cho movies và showtimes.
"""
from fastapi import APIRouter, HTTPException
from typing import List, Dict
from app.models import MovieBase, MovieCreate, Movie, MovieUpdate, ShowtimeCreate, Showtime
from app.database import (
    get_movie_by_id,
    create_movie,
    update_movie,
    delete_movie,
    get_all_movies,
    create_showtime,
    get_showtime_by_id,
    get_movie_showtimes,
    update_showtime,
    delete_showtime
)
import logging

logger = logging.getLogger("movie-service")

router = APIRouter(tags=["movies"])

# Movie routes
@router.get("/movies", response_model=List[Movie])
async def get_movies():
    """Lấy danh sách tất cả phim."""
    try:
        return await get_all_movies()
    except Exception as e:
        logger.error(f"Error retrieving movies: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/movies/{movie_id}", response_model=Movie)
async def get_movie_endpoint(movie_id: str):
    """Lấy thông tin chi tiết của một phim."""
    try:
        movie = await get_movie_by_id(movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        return movie
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving movie: {e}")
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

@router.post("/movies", response_model=Movie)
async def create_movie_endpoint(movie: MovieCreate):
    """Tạo một phim mới."""
    try:
        movie_dict = movie.dict()
        result = await create_movie(movie_dict)
        return result
    except Exception as e:
        logger.error(f"Error creating movie: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/movies/{movie_id}", response_model=Dict[str, str])
async def update_movie_endpoint(movie_id: str, movie: MovieUpdate):
    """Cập nhật thông tin phim."""
    try:
        success = await update_movie(movie_id, movie.dict(exclude_unset=True))
        if not success:
            raise HTTPException(status_code=404, detail="Movie not found")
        return {"message": "Movie updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating movie: {e}")
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

@router.delete("/movies/{movie_id}", response_model=Dict[str, str])
async def delete_movie_endpoint(movie_id: str):
    """Xoá một phim."""
    try:
        success = await delete_movie(movie_id)
        if not success:
            raise HTTPException(status_code=404, detail="Movie not found")
        return {"message": "Movie deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting movie: {e}")
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

# Showtime routes
@router.post("/showtimes", response_model=Showtime)
async def create_showtime_endpoint(showtime: ShowtimeCreate):
    """Tạo một lịch chiếu mới."""
    try:
        # Kiểm tra xem phim có tồn tại không
        movie = await get_movie_by_id(showtime.movie_id)
        if not movie:
            raise HTTPException(status_code=404, detail="Movie not found")
        
        showtime_dict = showtime.dict()
        result = await create_showtime(showtime_dict)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating showtime: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/showtimes/{showtime_id}", response_model=Showtime)
async def get_showtime_endpoint(showtime_id: str):
    """Lấy thông tin chi tiết của một lịch chiếu."""
    try:
        showtime = await get_showtime_by_id(showtime_id)
        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")
        return showtime
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving showtime: {e}")
        raise HTTPException(status_code=400, detail="Invalid showtime ID format")

@router.get("/showtimes/movie/{movie_id}", response_model=List[Showtime])
async def get_movie_showtimes_endpoint(movie_id: str):
    """Lấy tất cả lịch chiếu của một phim."""
    try:
        return await get_movie_showtimes(movie_id)
    except Exception as e:
        logger.error(f"Error retrieving movie showtimes: {e}")
        raise HTTPException(status_code=400, detail="Invalid movie ID format")

@router.put("/showtimes/{showtime_id}", response_model=Dict[str, str])
async def update_showtime_endpoint(showtime_id: str, showtime: ShowtimeCreate):
    """Cập nhật thông tin lịch chiếu."""
    try:
        success = await update_showtime(showtime_id, showtime.dict())
        if not success:
            raise HTTPException(status_code=404, detail="Showtime not found")
        return {"message": "Showtime updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating showtime: {e}")
        raise HTTPException(status_code=400, detail="Invalid showtime ID format")

@router.delete("/showtimes/{showtime_id}", response_model=Dict[str, str])
async def delete_showtime_endpoint(showtime_id: str):
    """Xoá một lịch chiếu."""
    try:
        success = await delete_showtime(showtime_id)
        if not success:
            raise HTTPException(status_code=404, detail="Showtime not found")
        return {"message": "Showtime deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting showtime: {e}")
        raise HTTPException(status_code=400, detail="Invalid showtime ID format") 