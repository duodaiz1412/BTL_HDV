from fastapi import FastAPI, HTTPException, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
import aioboto3
from botocore.exceptions import ClientError
import json
from bson import ObjectId
import asyncio
import httpx
import logging

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("booking-service")

load_dotenv()

app = FastAPI(title="Booking Service")

# MongoDB connection
# Sử dụng URI của MongoDB Atlas nếu có, nếu không thì dùng kết nối local
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.booking_db

# SQS Session
sqs_session = None

# SQS Queue URLs
BOOKING_CREATED_QUEUE_URL = os.getenv('SQS_BOOKING_CREATED_URL')
PAYMENT_PROCESSED_QUEUE_URL = os.getenv('SQS_PAYMENT_PROCESSED_URL')
SEATS_BOOKED_QUEUE_URL = os.getenv('SQS_SEATS_BOOKED_URL')

# Models
class SeatInfo(BaseModel):
    seat_id: str
    seat_number: str

class BookingBase(BaseModel):
    customer_id: str
    movie_id: str
    showtime_id: str
    showtime: str
    seats: List[SeatInfo]  # Danh sách các seat chứa cả seat_id và seat_number
    total_amount: float
    status: str = "pending"

# Helper functions
def convert_mongo_id(booking):
    booking["_id"] = str(booking["_id"])
    if "created_at" in booking and isinstance(booking["created_at"], datetime):
        booking["created_at"] = booking["created_at"].isoformat()
    return booking

async def get_sqs_session():
    """Tạo và trả về phiên aioboto3 được chia sẻ"""
    global sqs_session
    if sqs_session is None:
        sqs_session = aioboto3.Session(
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
    return sqs_session

async def send_sqs_message(queue_url, message):
    try:
        session = await get_sqs_session()
        async with session.resource('sqs') as sqs_resource:
            queue = await sqs_resource.get_queue_by_url(QueueUrl=queue_url)
            await queue.send_message(MessageBody=json.dumps(message))
            logger.info(f"Message sent to SQS queue: {queue_url}")
            return True
    except Exception as e:
        logger.error(f"Error sending message to SQS: {e}")
        return False

# Routes
@app.post("/bookings", response_model=Dict[str, Any])
async def create_booking(booking: BookingBase, background_tasks: BackgroundTasks):
    try:
        # Create booking in MongoDB
        booking_dict = booking.dict()
        booking_dict["created_at"] = datetime.utcnow()
        result = await db.bookings.insert_one(booking_dict)
        booking_dict["_id"] = str(result.inserted_id)

        # Convert datetime to string for SQS message
        sqs_message = booking_dict.copy()
        sqs_message["created_at"] = sqs_message["created_at"].isoformat()

        # Send message to SQS in background task
        background_tasks.add_task(send_sqs_message, BOOKING_CREATED_QUEUE_URL, sqs_message)
        
        # Cập nhật trạng thái ghế thành "pending" trong background task
        async def update_seats():
            async with httpx.AsyncClient() as client:
                for seat in booking.seats:
                    try:
                        await client.put(
                            f"{os.getenv('SEAT_SERVICE_URL', 'http://seat-service:8000')}/seats/{seat.seat_id}/status",
                            params={"status": "pending"}
                        )
                    except Exception as e:
                        logger.error(f"Error updating seat status: {e}")
        
        background_tasks.add_task(update_seats)
        
        return convert_mongo_id(booking_dict)
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookings/{booking_id}", response_model=Dict[str, Any])
async def get_booking(booking_id: str):
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return convert_mongo_id(booking)
    except Exception as e:
        logger.error(f"Error retrieving booking: {e}")
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

@app.get("/bookings/customer/{customer_id}", response_model=List[Dict[str, Any]])
async def get_customer_bookings(customer_id: str):
    try:
        bookings = await db.bookings.find({"customer_id": customer_id}).to_list(length=None)
        return [convert_mongo_id(booking) for booking in bookings]
    except Exception as e:
        logger.error(f"Error retrieving customer bookings: {e}")
        return []

@app.put("/bookings/{booking_id}/status", response_model=Dict[str, str])
async def update_booking_status(booking_id: str, status: str, background_tasks: BackgroundTasks):
    try:
        result = await db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"status": status}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Nếu status là confirmed, gửi thông báo đến SQS
        if status == "confirmed":
            booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
            if booking:
                booking_message = convert_mongo_id(booking)
                background_tasks.add_task(send_sqs_message, SEATS_BOOKED_QUEUE_URL, booking_message)
        
        return {"message": "Booking status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating booking status: {e}")
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

@app.get("/showtimes", response_model=List[Dict[str, Any]])
async def get_all_showtimes():
    showtimes = await db.showtimes.find().to_list(length=None)
    return [convert_mongo_id(showtime) for showtime in showtimes]

@app.get("/seats", response_model=List[Dict[str, Any]])
async def get_all_seats():
    seats = await db.seats.find().to_list(length=None)
    return [convert_mongo_id(seat) for seat in seats]

@app.get("/payments", response_model=List[Dict[str, Any]])
async def get_all_payments():
    payments = await db.payments.find().to_list(length=None)
    return [convert_mongo_id(payment) for payment in payments]

@app.get("/notifications", response_model=List[Dict[str, Any]])
async def get_all_notifications():
    notifications = await db.notifications.find().to_list(length=None)
    return [convert_mongo_id(notification) for notification in notifications]

@app.on_event("shutdown")
async def shutdown_event():
    global sqs_session
    # Đóng SQS session khi shutdown
    sqs_session = None 