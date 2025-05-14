"""
MongoDB connection và functions.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import MONGODB_URI
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger("movie-service")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.movie_db

def convert_mongo_id(item):
    """Convert MongoDB ObjectId to string."""
    if item:
        item["id"] = str(item.pop("_id"))
    return item

# Movie functions
async def get_all_movies():
    """Get all movies."""
    try:
        movies = await db.movies.find().to_list(length=None)
        return [convert_mongo_id(movie) for movie in movies]
    except Exception as e:
        logger.error(f"Error retrieving all movies: {e}")
        return []

async def get_movie_by_id(movie_id: str):
    """Get a movie by ID."""
    try:
        movie = await db.movies.find_one({"_id": ObjectId(movie_id)})
        if movie:
            return convert_mongo_id(movie)
        return None
    except Exception as e:
        logger.error(f"Error retrieving movie by ID: {e}")
        return None

async def create_movie(movie_data: dict):
    """Create a new movie."""
    try:
        movie_data["created_at"] = datetime.now()
        result = await db.movies.insert_one(movie_data)
        movie_data["_id"] = result.inserted_id
        return convert_mongo_id(movie_data)
    except Exception as e:
        logger.error(f"Error creating movie: {e}")
        raise e

async def update_movie(movie_id: str, movie_data: dict):
    """Update a movie."""
    try:
        # Chỉ cập nhật các field có giá trị
        update_data = {k: v for k, v in movie_data.items() if v is not None}
        
        result = await db.movies.update_one(
            {"_id": ObjectId(movie_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating movie: {e}")
        return False

async def delete_movie(movie_id: str):
    """Delete a movie."""
    try:
        result = await db.movies.delete_one({"_id": ObjectId(movie_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting movie: {e}")
        return False

# Showtime functions
async def create_showtime(showtime_data: dict):
    """Create a new showtime."""
    try:
        showtime_data["created_at"] = datetime.now()
        result = await db.showtimes.insert_one(showtime_data)
        showtime_data["_id"] = result.inserted_id
        return convert_mongo_id(showtime_data)
    except Exception as e:
        logger.error(f"Error creating showtime: {e}")
        raise e

async def get_showtime_by_id(showtime_id: str):
    """Get a showtime by ID."""
    try:
        showtime = await db.showtimes.find_one({"_id": ObjectId(showtime_id)})
        if showtime:
            return convert_mongo_id(showtime)
        return None
    except Exception as e:
        logger.error(f"Error retrieving showtime by ID: {e}")
        return None

async def get_movie_showtimes(movie_id: str):
    """Get all showtimes for a movie."""
    try:
        showtimes = await db.showtimes.find({"movie_id": movie_id}).to_list(length=None)
        return [convert_mongo_id(showtime) for showtime in showtimes]
    except Exception as e:
        logger.error(f"Error retrieving movie showtimes: {e}")
        return []

async def update_showtime(showtime_id: str, showtime_data: dict):
    """Update a showtime."""
    try:
        result = await db.showtimes.update_one(
            {"_id": ObjectId(showtime_id)},
            {"$set": showtime_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating showtime: {e}")
        return False

async def delete_showtime(showtime_id: str):
    """Delete a showtime."""
    try:
        result = await db.showtimes.delete_one({"_id": ObjectId(showtime_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting showtime: {e}")
        return False 