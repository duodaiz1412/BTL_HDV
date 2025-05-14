from fastapi import FastAPI, HTTPException, BackgroundTasks
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import os
from dotenv import load_dotenv
import aioboto3
from botocore.exceptions import ClientError
import json
from bson import ObjectId
import logging
import uvicorn
from app.main import app

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("payment-service")

load_dotenv()

app = FastAPI(title="Payment Service")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.payment_db

# SQS Session
sqs_session = None

# SQS Queue URLs
PAYMENT_PROCESSED_QUEUE_URL = os.getenv('SQS_PAYMENT_PROCESSED_URL')

# Models
class PaymentBase(BaseModel):
    booking_id: str
    amount: float
    payment_method: str
    status: str = "pending"

# Helper functions
def convert_mongo_id(payment):
    payment["_id"] = str(payment["_id"])
    if "created_at" in payment and isinstance(payment["created_at"], datetime):
        payment["created_at"] = payment["created_at"].isoformat()
    return payment

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
        async with session.client('sqs') as sqs_client:
            await sqs_client.send_message(
                QueueUrl=queue_url,
                MessageBody=json.dumps(message)
            )
            logger.info(f"Message sent to SQS queue: {queue_url}")
            return True
    except Exception as e:
        logger.error(f"Error sending message to SQS: {e}")
        return False

# Routes
@app.post("/payments", response_model=Dict[str, Any])
async def create_payment(payment: PaymentBase, background_tasks: BackgroundTasks):
    try:
        # Create payment in MongoDB
        payment_dict = payment.dict()
        payment_dict["created_at"] = datetime.utcnow()
        result = await db.payments.insert_one(payment_dict)
        payment_dict["_id"] = str(result.inserted_id)

        # Convert datetime to string for SQS message
        sqs_message = payment_dict.copy()
        sqs_message["created_at"] = sqs_message["created_at"].isoformat()

        # Send message to SQS in background task
        background_tasks.add_task(send_sqs_message, PAYMENT_PROCESSED_QUEUE_URL, sqs_message)
        
        return convert_mongo_id(payment_dict)
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/payments/{payment_id}", response_model=Dict[str, Any])
async def get_payment(payment_id: str):
    try:
        payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        return convert_mongo_id(payment)
    except Exception as e:
        logger.error(f"Error retrieving payment: {e}")
        raise HTTPException(status_code=400, detail="Invalid payment ID format")

@app.get("/payments/booking/{booking_id}", response_model=List[Dict[str, Any]])
async def get_booking_payments(booking_id: str):
    try:
        payments = await db.payments.find({"booking_id": booking_id}).to_list(length=None)
        return [convert_mongo_id(payment) for payment in payments]
    except Exception as e:
        logger.error(f"Error retrieving booking payments: {e}")
        return []

@app.put("/payments/{payment_id}/status", response_model=Dict[str, str])
async def update_payment_status(payment_id: str, status: str, background_tasks: BackgroundTasks):
    try:
        result = await db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {"status": status}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Payment not found")
            
        # Nếu status là completed, gửi thông báo đến SQS
        if status == "completed":
            payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
            if payment:
                payment_message = convert_mongo_id(payment)
                background_tasks.add_task(send_sqs_message, PAYMENT_PROCESSED_QUEUE_URL, payment_message)
                
        return {"message": "Payment status updated successfully"}
    except Exception as e:
        logger.error(f"Error updating payment status: {e}")
        raise HTTPException(status_code=400, detail="Invalid payment ID format")

@app.post("/payments/{payment_id}/refund", response_model=Dict[str, Any])
async def refund_payment(payment_id: str, background_tasks: BackgroundTasks):
    try:
        payment = await db.payments.find_one({"_id": ObjectId(payment_id)})
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")

        if payment["status"] != "completed":
            raise HTTPException(status_code=400, detail="Payment is not completed")

        # Simulate refund processing
        # In a real application, this would integrate with a payment gateway
        refund_id = f"REF_{payment_id}"

        # Update payment status
        await db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {
                "$set": {
                    "status": "refunded",
                    "refund_id": refund_id
                }
            }
        )

        # Send event to SQS in background task
        refund_message = {
            "payment_id": payment_id,
            "booking_id": payment["booking_id"],
            "refund_id": refund_id,
            "status": "refunded",
            "amount": payment.get("amount", 0)
        }
        background_tasks.add_task(send_sqs_message, PAYMENT_PROCESSED_QUEUE_URL, refund_message)

        return {
            "message": "Payment refunded successfully",
            "refund_id": refund_id
        }
    except Exception as e:
        logger.error(f"Error refunding payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown_event():
    global sqs_session
    # Đóng SQS session khi shutdown
    sqs_session = None

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 