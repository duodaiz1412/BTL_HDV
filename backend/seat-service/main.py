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

load_dotenv()

app = FastAPI(title="Seat Service")

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.seat_db

# Kafka producer
kafka_producer = None

async def get_kafka_producer():
    global kafka_producer
    if kafka_producer is None:
        kafka_producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
        )
        await kafka_producer.start()
    return kafka_producer

# Models
class Seat(BaseModel):
    showtime_id: str
    seat_number: str
    status: str = "available"
    price: float

# Helper functions
def convert_mongo_id(seat):
    if seat:
        seat["id"] = str(seat["_id"])
        del seat["_id"]
    return seat

# Routes
@app.post("/seats")
async def create_seat(seat: Seat):
    seat_dict = seat.dict()
    seat_dict["created_at"] = datetime.now().isoformat()
    
    result = await db.seats.insert_one(seat_dict)
    seat_dict["id"] = str(result.inserted_id)
    del seat_dict["_id"]
    
    return seat_dict

@app.get("/seats/{seat_id}")
async def get_seat(seat_id: str):
    try:
        seat = await db.seats.find_one({"_id": ObjectId(seat_id)})
        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")
        return convert_mongo_id(seat)
    except:
        raise HTTPException(status_code=400, detail="Invalid seat ID format")

@app.get("/seats/showtime/{showtime_id}")
async def get_showtime_seats(showtime_id: str):
    seats = await db.seats.find({"showtime_id": showtime_id}).to_list(length=None)
    return [convert_mongo_id(seat) for seat in seats]

@app.put("/seats/{seat_id}/status")
async def update_seat_status(seat_id: str, status: str):
    try:
        result = await db.seats.update_one(
            {"_id": ObjectId(seat_id)},
            {"$set": {"status": status}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Seat not found")
        return {"message": "Seat status updated successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid seat ID format")

@app.post("/seats/check")
async def check_seats(showtime_id: str, seats: List[str]):
    # Check if seats are available
    unavailable_seats = await db.seats.find({
        "showtime_id": showtime_id,
        "seat_number": {"$in": seats},
        "status": "booked"
    }).to_list(length=None)
    
    if unavailable_seats:
        raise HTTPException(status_code=400, detail="Some seats are already booked")
    
    return {"message": "Seats are available"}

@app.post("/seats/book")
async def book_seats(showtime_id: str, seats: List[str], booking_id: str):
    # Book seats
    result = await db.seats.update_many(
        {
            "showtime_id": showtime_id,
            "seat_number": {"$in": seats}
        },
        {
            "$set": {
                "status": "booked",
                "booking_id": booking_id
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to book seats")
    
    # Send event to Kafka
    producer = await get_kafka_producer()
    await producer.send_and_wait(
        "seats_booked",
        json.dumps({
            "showtime_id": showtime_id,
            "seats": seats,
            "booking_id": booking_id
        }).encode()
    )
    
    return {"message": "Seats booked successfully"}

@app.post("/seats/release")
async def release_seats(showtime_id: str, seats: List[str]):
    # Release seats
    result = await db.seats.update_many(
        {
            "showtime_id": showtime_id,
            "seat_number": {"$in": seats}
        },
        {
            "$set": {
                "status": "available",
                "booking_id": None
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to release seats")
    
    return {"message": "Seats released successfully"}

@app.on_event("shutdown")
async def shutdown_event():
    if kafka_producer:
        await kafka_producer.stop() 