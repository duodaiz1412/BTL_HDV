"""
Database connection module for seat service.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import MONGODB_URI
from bson import ObjectId
from datetime import datetime

# MongoDB connection
client = AsyncIOMotorClient(MONGODB_URI)
db = client.seat_db

def convert_mongo_id(seat):
    """Convert MongoDB ObjectId to string and format datetime objects."""
    seat["id"] = str(seat.pop("_id"))
    if "created_at" in seat and isinstance(seat["created_at"], datetime):
        seat["created_at"] = seat["created_at"].isoformat()
    return seat

# Helper functions
async def get_seats_collection():
    return db.seats

async def get_seat_by_id(seat_id: str):
    """Get a seat by its ID."""
    try:
        seat = await db.seats.find_one({"_id": ObjectId(seat_id)})
        if seat:
            return convert_mongo_id(seat)
        return None
    except Exception:
        return None

async def get_all_seats():
    """Get all seats."""
    seats = await db.seats.find().to_list(length=None)
    return [convert_mongo_id(seat) for seat in seats]

async def create_seat(seat_data: dict):
    """Create a new seat."""
    seat_data["created_at"] = datetime.utcnow()
    result = await db.seats.insert_one(seat_data)
    seat_data["_id"] = result.inserted_id
    return convert_mongo_id(seat_data)

async def update_seat_status(seat_id: str, status: str):
    """Update the status of a seat."""
    result = await db.seats.update_one(
        {"_id": ObjectId(seat_id)},
        {"$set": {"status": status}}
    )
    return result.modified_count > 0 