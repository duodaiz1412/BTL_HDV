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

load_dotenv()

app = FastAPI(title="Seat Service")

# MongoDB connection
# Sử dụng URI của MongoDB Atlas nếu có, nếu không thì dùng kết nối local
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.seat_db

# AWS SQS client
sqs = boto3.client('sqs',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

# SQS Queue URLs
SEATS_BOOKED_QUEUE_URL = os.getenv('SQS_SEATS_BOOKED_URL')

# Models
class SeatBase(BaseModel):
    showtime_id: str
    seat_number: str
    status: str = "available"

# Helper functions
def convert_mongo_id(seat):
    seat["_id"] = str(seat["_id"])
    return seat

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
@app.post("/seats")
async def create_seat(seat: SeatBase):
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
    try:
        # Check if seats are available
        for seat_number in seats:
            seat = await db.seats.find_one({
                "showtime_id": showtime_id,
                "seat_number": seat_number,
                "status": "available"
            })
            if not seat:
                raise HTTPException(status_code=400, detail=f"Seat {seat_number} is not available")
        return {"message": "All seats are available"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/seats/book")
async def book_seats(showtime_id: str, seats: List[str]):
    try:
        # Check seats availability first
        await check_seats(showtime_id, seats)
        
        # Update seats status
        result = await db.seats.update_many(
            {
                "showtime_id": showtime_id,
                "seat_number": {"$in": seats}
            },
            {"$set": {"status": "booked", "booked_at": datetime.utcnow()}}
        )
        
        if result.modified_count != len(seats):
            raise HTTPException(status_code=500, detail="Failed to book all seats")
        
        # Send message to SQS
        await send_sqs_message(SEATS_BOOKED_QUEUE_URL, {
            "showtime_id": showtime_id,
            "seats": seats,
            "booked_at": datetime.utcnow().isoformat()
        })
        
        return {"message": "Seats booked successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/seats")
async def get_all_seats():
    seats = await db.seats.find().to_list(length=None)
    return [convert_mongo_id(seat) for seat in seats]

@app.post("/seats/initialize")
async def initialize_seats(showtime_id: str, total_seats: int):
    try:
        # Create seats for the showtime
        seats = []
        for i in range(1, total_seats + 1):
            seat = {
                "showtime_id": showtime_id,
                "seat_number": f"A{i}",
                "status": "available",
                "created_at": datetime.utcnow()
            }
            seats.append(seat)
        
        result = await db.seats.insert_many(seats)
        return {"message": f"Initialized {len(result.inserted_ids)} seats"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/seats/create-for-showtime")
async def create_seats_for_showtime(showtime_id: str):
    try:
        # Kiểm tra xem đã có ghế cho showtime này chưa
        existing_seats = await db.seats.find({"showtime_id": showtime_id}).to_list(length=None)
        if existing_seats:
            return {"message": f"Seats already exist for showtime {showtime_id}", "seats_count": len(existing_seats)}
        
        # Tạo danh sách các ghế từ A1-E10
        rows = ['A', 'B', 'C', 'D', 'E']
        seats = []
        
        for row in rows:
            for num in range(1, 11):  # 1-10
                seat = {
                    "showtime_id": showtime_id,
                    "seat_number": f"{row}{num}",
                    "status": "available",
                    "created_at": datetime.utcnow()
                }
                seats.append(seat)
        
        # Lưu tất cả ghế vào database
        result = await db.seats.insert_many(seats)
        
        # Gửi thông báo qua SQS (nếu cần thiết)
        # await send_sqs_message(SEATS_BOOKED_QUEUE_URL, {
        #     "showtime_id": showtime_id,
        #     "action": "seats_created",
        #     "count": len(result.inserted_ids)
        # })
        
        return {
            "message": f"Created {len(result.inserted_ids)} seats for showtime {showtime_id}",
            "seat_count": len(result.inserted_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    # No need to stop SQS client as it's managed by AWS
    pass 