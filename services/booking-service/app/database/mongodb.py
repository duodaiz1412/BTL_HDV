from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import MONGODB_URI
from bson import ObjectId
from datetime import datetime, timedelta
from app.utils.datetime_utils import (
    get_utc_now, convert_to_hanoi_timezone, 
    format_mongodb_datetime, create_datetime_metadata
)

client = AsyncIOMotorClient(MONGODB_URI)
db = client.booking_db

def convert_mongo_id(booking):
    """Convert MongoDB ObjectId to string and format datetime objects."""
    booking["id"] = str(booking.pop("_id"))
    if "created_at" in booking and isinstance(booking["created_at"], datetime):
        # Sử dụng hàm tiện ích để chuyển đổi và định dạng thời gian
        booking["created_at_formatted"] = format_mongodb_datetime(booking["created_at"])
        booking["created_at"] = booking["created_at"].isoformat()
    return booking

async def get_booking_by_id(booking_id: str):
    """Get a booking by its ID."""
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if booking:
            return convert_mongo_id(booking)
        return None
    except Exception:
        return None

async def get_bookings_by_customer(customer_id: str):
    """Get all bookings for a specific customer."""
    bookings = await db.bookings.find({"customer_id": customer_id}).to_list(length=None)
    return [convert_mongo_id(booking) for booking in bookings]

async def create_booking(booking_data: dict):
    """Create a new booking."""
    # Sử dụng tiện ích để tạo thông tin thời gian
    utc_now = get_utc_now()
    booking_data["created_at"] = utc_now
    booking_data["datetime_metadata"] = create_datetime_metadata(utc_now)
    
    result = await db.bookings.insert_one(booking_data)
    booking_data["_id"] = result.inserted_id
    return convert_mongo_id(booking_data)

async def update_booking_status(booking_id: str, status: str):
    """Update the status of a booking."""
    result = await db.bookings.update_one(
        {"_id": ObjectId(booking_id)},
        {"$set": {"status": status}}
    )
    return result.modified_count > 0

async def get_all_showtimes():
    """Get all showtimes."""
    showtimes = await db.showtimes.find().to_list(length=None)
    return [convert_mongo_id(showtime) for showtime in showtimes]

async def get_all_seats():
    """Get all seats."""
    seats = await db.seats.find().to_list(length=None)
    return [convert_mongo_id(seat) for seat in seats]

async def get_all_payments():
    """Get all payments."""
    payments = await db.payments.find().to_list(length=None)
    return [convert_mongo_id(payment) for payment in payments]

async def get_all_notifications():
    """Get all notifications."""
    notifications = await db.notifications.find().to_list(length=None)
    return [convert_mongo_id(notification) for notification in notifications] 