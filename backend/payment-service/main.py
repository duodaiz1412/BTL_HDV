from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
import json
from bson import ObjectId

load_dotenv()

app = FastAPI(title="Payment Service")

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.payment_db

# AWS SQS client
sqs = boto3.client('sqs',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

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
@app.post("/payments")
async def create_payment(payment: PaymentBase):
    try:
        # Create payment in MongoDB
        payment_dict = payment.dict()
        payment_dict["created_at"] = datetime.utcnow()
        result = await db.payments.insert_one(payment_dict)
        payment_dict["_id"] = str(result.inserted_id)

        # Convert datetime to string for SQS message
        sqs_message = payment_dict.copy()
        sqs_message["created_at"] = sqs_message["created_at"].isoformat()

        # Send message to SQS
        await send_sqs_message(PAYMENT_PROCESSED_QUEUE_URL, sqs_message)
        
        return convert_mongo_id(payment_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

    # Send event to SQS
    await send_sqs_message(PAYMENT_PROCESSED_QUEUE_URL, {
        "payment_id": payment_id,
        "booking_id": payment["booking_id"],
        "refund_id": refund_id
    })

    return {
        "message": "Payment refunded successfully",
        "refund_id": refund_id
    }

@app.on_event("shutdown")
async def shutdown_event():
    # No need to stop SQS client as it's managed by AWS
    pass 