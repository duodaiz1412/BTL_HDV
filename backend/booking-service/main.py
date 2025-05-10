from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import aiokafka
import json
from bson import ObjectId
import asyncio

load_dotenv()

app = FastAPI(title="Booking Service")

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.booking_db

# Kafka producer
kafka_producer = None

async def get_kafka_producer():
    global kafka_producer
    if kafka_producer is None:
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries:
            try:
                kafka_producer = aiokafka.AIOKafkaProducer(
                    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
                    retry_backoff_ms=500,
                    request_timeout_ms=30000
                )
                await kafka_producer.start()
                return kafka_producer
            except Exception as e:
                retry_count += 1
                print(f"Failed to connect to Kafka (attempt {retry_count}/{max_retries}): {e}")
                if retry_count == max_retries:
                    print("Max retries reached. Starting service without Kafka producer.")
                    return None
                await asyncio.sleep(5)  # Wait 5 seconds before retrying
    return kafka_producer

# Models
class BookingCreate(BaseModel):
    customer_id: str
    movie_id: str
    showtime_id: str
    seats: List[str]
    total_amount: float
    status: str = "pending"

class Booking(BookingCreate):
    payment_id: Optional[str] = None

# Helper functions
def convert_mongo_id(booking):
    if booking:
        booking["id"] = str(booking["_id"])
        del booking["_id"]
    return booking

# Routes
@app.post("/bookings")
async def create_booking(booking: BookingCreate):
    booking_dict = booking.dict()
    booking_dict["created_at"] = datetime.now().isoformat()
    result = await db.bookings.insert_one(booking_dict)
    booking_dict["id"] = str(result.inserted_id)
    if "_id" in booking_dict:
        del booking_dict["_id"]
    
    try:
        producer = await get_kafka_producer()
        if producer:
            await producer.send_and_wait(
                "booking_created",
                json.dumps(booking_dict).encode()
            )
    except Exception as e:
        print(f"Error sending message to Kafka: {e}")
    
    return booking_dict

@app.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    try:
        booking = await db.bookings.find_one({"_id": ObjectId(booking_id)})
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return convert_mongo_id(booking)
    except:
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

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

@app.get("/bookings/customer/{customer_id}")
async def get_customer_bookings(customer_id: str):
    bookings = await db.bookings.find({"customer_id": customer_id}).to_list(length=None)
    return [convert_mongo_id(booking) for booking in bookings]

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
    if kafka_producer:
        await kafka_producer.stop() 