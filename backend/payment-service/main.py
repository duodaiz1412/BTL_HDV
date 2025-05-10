from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import aiokafka
import json
from bson import ObjectId

load_dotenv()

app = FastAPI(title="Payment Service")

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.payment_db

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
class Payment(BaseModel):
    booking_id: str
    amount: float
    payment_method: str
    status: str = "pending"

# Helper functions
def convert_mongo_id(payment):
    if payment:
        payment["id"] = str(payment["_id"])
        del payment["_id"]
    return payment

# Routes
@app.post("/payments")
async def create_payment(payment: Payment):
    payment_dict = payment.dict()
    payment_dict["created_at"] = datetime.now().isoformat()
    
    result = await db.payments.insert_one(payment_dict)
    payment_dict["id"] = str(result.inserted_id)
    del payment_dict["_id"]
    
    # Send notification
    producer = await get_kafka_producer()
    await producer.send_and_wait(
        "payment_processed",
        json.dumps(payment_dict).encode()
    )
    
    return payment_dict

@app.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    try:
        payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return convert_mongo_id(payment)
    except:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")

@app.get("/payments/booking/{booking_id}")
async def get_booking_payments(booking_id: str):
    payments = await db.payments.find({"booking_id": booking_id}).to_list(length=None)
    return [convert_mongo_id(payment) for payment in payments]

@app.put("/payments/{payment_id}/status")
async def update_payment_status(payment_id: str, status: str):
    try:
        result = await db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {"status": status}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Payment not found")
        return {"message": "Payment status updated successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid payment ID format")

@app.post("/payments/{payment_id}/refund")
async def refund_payment(payment_id: str):
    payment = await db.payments.find_one({"_id": payment_id})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment["status"] != "completed":
        raise HTTPException(status_code=400, detail="Payment is not completed")

    # Simulate refund processing
    # In a real application, this would integrate with a payment gateway
    refund_id = f"REF_{payment_id}"

    # Update payment status
    await db.payments.update_one(
        {"_id": payment_id},
        {
            "$set": {
                "status": "refunded",
                "refund_id": refund_id
            }
        }
    )

    # Send event to Kafka
    producer = await get_kafka_producer()
    await producer.send_and_wait(
        "payment_refunded",
        json.dumps({
            "payment_id": payment_id,
            "booking_id": payment["booking_id"],
            "refund_id": refund_id
        }).encode()
    )

    return {
        "message": "Payment refunded successfully",
        "refund_id": refund_id
    }

@app.on_event("shutdown")
async def shutdown_event():
    if kafka_producer:
        await kafka_producer.stop() 