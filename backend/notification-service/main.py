from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import aiokafka
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

# Kafka consumer
kafka_consumer = None

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

async def get_kafka_consumer():
    global kafka_consumer
    if kafka_consumer is None:
        max_retries = 5
        retry_count = 0
        while retry_count < max_retries:
            try:
                kafka_consumer = aiokafka.AIOKafkaConsumer(
                    "booking_created",
                    "payment_processed",
                    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092"),
                    group_id="notification-service",
                    retry_backoff_ms=500,
                    request_timeout_ms=30000
                )
                await kafka_consumer.start()
                return kafka_consumer
            except Exception as e:
                retry_count += 1
                print(f"Failed to connect to Kafka (attempt {retry_count}/{max_retries}): {e}")
                if retry_count == max_retries:
                    print("Max retries reached. Starting service without Kafka consumer.")
                    return None
                await asyncio.sleep(5)  # Wait 5 seconds before retrying
    return kafka_consumer

# Models
class Notification(BaseModel):
    customer_id: str
    type: str
    message: str
    status: str = "pending"
    sent_at: Optional[datetime] = None

# Helper functions
def convert_mongo_id(notification):
    if notification:
        notification["id"] = str(notification["_id"])
        del notification["_id"]
    return notification

# Routes
@app.post("/notifications")
async def create_notification(notification: Notification):
    notification_dict = notification.dict()
    notification_dict["created_at"] = datetime.now().isoformat()
    
    result = await db.notifications.insert_one(notification_dict)
    notification_dict["id"] = str(result.inserted_id)
    del notification_dict["_id"]
    
    return notification_dict

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

async def process_booking_notification(booking_data):
    # Get customer and movie details
    customer = await db.customers.find_one({"_id": booking_data["customer_id"]})
    movie = await db.movies.find_one({"_id": booking_data["movie_id"]})
    
    if not customer or not movie:
        return
    
    # Prepare email content
    template = Template(email_template)
    email_content = template.render(
        customer_name=customer["name"],
        movie_title=movie["title"],
        showtime=booking_data["showtime"],
        seats=", ".join(booking_data["seats"]),
        total_amount=booking_data["total_amount"]
    )
    
    # Send email (simulated)
    # In a real application, this would use an email service
    print(f"Sending email to {customer['email']}:")
    print(email_content)
    
    # Create notification record
    notification = Notification(
        customer_id=customer["_id"],
        type="booking_confirmation",
        message=email_content,
        status="sent",
        sent_at=datetime.now().isoformat()
    )
    await db.notifications.insert_one(notification.dict())

async def process_payment_notification(payment_data):
    # Get booking details
    booking = await db.bookings.find_one({"_id": payment_data["booking_id"]})
    if not booking:
        return
    
    # Get customer details
    customer = await db.customers.find_one({"_id": booking["customer_id"]})
    if not customer:
        return
    
    # Prepare email content
    message = f"""
    Dear {customer['name']},
    
    Your payment for booking {booking['_id']} has been processed.
    Status: {payment_data['status']}
    Transaction ID: {payment_data['transaction_id']}
    
    Best regards,
    Movie Booking System
    """
    
    # Send email (simulated)
    # In a real application, this would use an email service
    print(f"Sending email to {customer['email']}:")
    print(message)
    
    # Create notification record
    notification = Notification(
        customer_id=customer["_id"],
        type="payment_confirmation",
        message=message,
        status="sent",
        sent_at=datetime.now().isoformat()
    )
    await db.notifications.insert_one(notification.dict())

@app.on_event("startup")
async def startup_event():
    try:
        consumer = await get_kafka_consumer()
        if consumer:
            asyncio.create_task(consume_messages(consumer))
    except Exception as e:
        print(f"Error starting Kafka consumer: {e}")

async def consume_messages(consumer):
    try:
        async for message in consumer:
            try:
                data = json.loads(message.value.decode())
                if message.topic == "booking_created":
                    await process_booking_notification(data)
                elif message.topic == "payment_processed":
                    await process_payment_notification(data)
            except Exception as e:
                print(f"Error processing message: {e}")
    except Exception as e:
        print(f"Error in consume_messages: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    if kafka_consumer:
        await kafka_consumer.stop() 