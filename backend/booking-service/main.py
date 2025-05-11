from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
import json
from bson import ObjectId
import asyncio

load_dotenv()

app = FastAPI(title="Booking Service")

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.booking_db

# AWS SQS client
sqs = boto3.client('sqs',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

# SQS Queue URLs
BOOKING_CREATED_QUEUE_URL = os.getenv('SQS_BOOKING_CREATED_URL')
PAYMENT_PROCESSED_QUEUE_URL = os.getenv('SQS_PAYMENT_PROCESSED_URL')
SEATS_BOOKED_QUEUE_URL = os.getenv('SQS_SEATS_BOOKED_URL')

# Models
class BookingBase(BaseModel):
    customer_id: str
    movie_id: str
    showtime_id: str
    seats: List[str]
    total_amount: float
    status: str = "pending"

# Helper functions
def convert_mongo_id(booking):
    booking["_id"] = str(booking["_id"])
    return booking

async def send_sqs_message(queue_url, message):
    try:
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message)
        )
        return response
    except ClientError as e:
        print(f"Error sending message to SQS: {e}")
        return None

# Routes
@app.post("/bookings")
async def create_booking(booking: BookingBase):
    try:
        # Create booking in MongoDB
        booking_dict = booking.dict()
        booking_dict["created_at"] = datetime.utcnow()
        result = await db.bookings.insert_one(booking_dict)
        booking_dict["_id"] = str(result.inserted_id)

        # Send message to SQS
        await send_sqs_message(BOOKING_CREATED_QUEUE_URL, booking_dict)
        
        return convert_mongo_id(booking_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return convert_mongo_id(booking)
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

@app.get("/bookings/customer/{customer_id}")
async def get_customer_bookings(customer_id: str):
    bookings = await db.bookings.find({"customer_id": customer_id}).to_list(length=None)
    return [convert_mongo_id(booking) for booking in bookings]

@app.put("/bookings/{booking_id}/status")
async def update_booking_status(booking_id: str, status: str):
    try:
        result = await db.bookings.update_one(
            {"_id": ObjectId(booking_id)},
            {"$set": {"status": status}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Booking not found")
        return {"message": "Booking status updated successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

@app.get("/showtimes")
async def get_all_showtimes():
    showtimes = await db.showtimes.find().to_list(length=None)
    return [convert_mongo_id(showtime) for showtime in showtimes]

@app.get("/seats")
async def get_all_seats():
    seats = await db.seats.find().to_list(length=None)
    return [convert_mongo_id(seat) for seat in seats]

@app.get("/payments")
async def get_all_payments():
    payments = await db.payments.find().to_list(length=None)
    return [convert_mongo_id(payment) for payment in payments]

@app.get("/notifications")
async def get_all_notifications():
    notifications = await db.notifications.find().to_list(length=None)
    return [convert_mongo_id(notification) for notification in notifications]

@app.on_event("shutdown")
async def shutdown_event():
    # No need to stop SQS client as it's managed by AWS
    pass 