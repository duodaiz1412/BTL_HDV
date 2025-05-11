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
import aiohttp
from jinja2 import Template
from bson import ObjectId
import asyncio

load_dotenv()

app = FastAPI(title="Notification Service")

# MongoDB connection
client = AsyncIOMotorClient(os.getenv("MONGODB_URI", "mongodb://localhost:27017"))
db = client.notification_db

# AWS SQS client
sqs = boto3.client('sqs',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

# SQS Queue URLs
BOOKING_CREATED_QUEUE_URL = os.getenv('SQS_BOOKING_CREATED_URL')
PAYMENT_PROCESSED_QUEUE_URL = os.getenv('SQS_PAYMENT_PROCESSED_URL')

# Models
class Notification(BaseModel):
    type: str
    customer_id: str
    content: str
    status: str = "pending"
    booking_id: Optional[str] = None
    payment_id: Optional[str] = None

# Email template
email_template = """
Dear {{ customer_name }},

Thank you for booking tickets with us!

Booking Details:
- Movie: {{ movie_title }}
- Showtime: {{ showtime }}
- Seats: {{ seats }}
- Total Amount: {{ total_amount }}

Your booking has been confirmed. Please arrive at least 15 minutes before the showtime.

Best regards,
Movie Booking System
"""

# Helper functions
def convert_mongo_id(notification):
    notification["_id"] = str(notification["_id"])
    return notification

async def receive_sqs_messages(queue_url):
    try:
        response = sqs.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20
        )
        return response.get('Messages', [])
    except ClientError as e:
        print(f"Error receiving messages from SQS: {e}")
        return []

async def delete_sqs_message(queue_url, receipt_handle):
    try:
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
    except ClientError as e:
        print(f"Error deleting message from SQS: {e}")

async def process_booking_notification(message):
    try:
        booking_data = json.loads(message['Body'])
        template = Template(email_template)
        email_content = template.render(
            customer_name=booking_data.get('customer_name', 'Customer'),
            movie_title=booking_data.get('movie_title', 'Movie'),
            showtime=booking_data.get('showtime', 'Showtime'),
            seats=booking_data.get('seats', []),
            total_amount=booking_data.get('total_amount', 0)
        )
        
        # Store notification in MongoDB
        notification = {
            "type": "booking_confirmation",
            "customer_id": booking_data.get('customer_id'),
            "booking_id": booking_data.get('_id'),
            "content": email_content,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        await db.notifications.insert_one(notification)
        
        # TODO: Send actual email using your email service
        print(f"Email would be sent: {email_content}")
        
    except Exception as e:
        print(f"Error processing booking notification: {e}")

async def process_payment_notification(message):
    try:
        payment_data = json.loads(message['Body'])
        # Process payment notification
        notification = {
            "type": "payment_confirmation",
            "customer_id": payment_data.get('customer_id'),
            "payment_id": payment_data.get('_id'),
            "content": f"Payment of {payment_data.get('amount', 0)} has been processed successfully.",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        await db.notifications.insert_one(notification)
        
    except Exception as e:
        print(f"Error processing payment notification: {e}")

# Background task to process SQS messages
async def process_sqs_messages():
    while True:
        try:
            # Process booking notifications
            booking_messages = await receive_sqs_messages(BOOKING_CREATED_QUEUE_URL)
            for message in booking_messages:
                await process_booking_notification(message)
                await delete_sqs_message(BOOKING_CREATED_QUEUE_URL, message['ReceiptHandle'])
            
            # Process payment notifications
            payment_messages = await receive_sqs_messages(PAYMENT_PROCESSED_QUEUE_URL)
            for message in payment_messages:
                await process_payment_notification(message)
                await delete_sqs_message(PAYMENT_PROCESSED_QUEUE_URL, message['ReceiptHandle'])
            
            await asyncio.sleep(1)  # Wait before next poll
        except Exception as e:
            print(f"Error in SQS message processing: {e}")
            await asyncio.sleep(5)  # Wait longer on error

# Routes
@app.post("/notifications")
async def create_notification(notification: Notification):
    notification_dict = notification.dict()
    notification_dict["created_at"] = datetime.utcnow()
    
    result = await db.notifications.insert_one(notification_dict)
    notification_dict["_id"] = str(result.inserted_id)
    
    return convert_mongo_id(notification_dict)

@app.get("/notifications/{notification_id}")
async def get_notification(notification_id: str):
    try:
        notification = await db.notifications.find_one({"_id": ObjectId(notification_id)})
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return convert_mongo_id(notification)
    except:
        raise HTTPException(status_code=400, detail="Invalid notification ID format")

@app.get("/notifications/customer/{customer_id}")
async def get_customer_notifications(customer_id: str):
    notifications = await db.notifications.find({"customer_id": customer_id}).to_list(length=None)
    return [convert_mongo_id(notification) for notification in notifications]

@app.put("/notifications/{notification_id}/status")
async def update_notification_status(notification_id: str, status: str):
    try:
        result = await db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"status": status}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        return {"message": "Notification status updated successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid notification ID format")

# Start background task
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_sqs_messages()) 