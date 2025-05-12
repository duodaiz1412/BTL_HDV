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
import socketio
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

# Khởi tạo Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    ping_timeout=20,  # Tăng timeout cho ping
    ping_interval=25,  # Giảm tần suất ping để giảm tải
    max_http_buffer_size=10e6,  # Tăng buffer size
    async_handlers=True,  # Đảm bảo xử lý bất đồng bộ
    logger=True,  # Bật logging để debug
    engineio_logger=True  # Bật engineio logging
)

# Khởi tạo FastAPI app
app = FastAPI(title="Notification Service")

# Thêm middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Kết hợp Socket.IO với FastAPI (quan trọng: đúng thứ tự)
socket_app = socketio.ASGIApp(sio, app)

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
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
        
        # Send real-time notification through Socket.IO
        await sio.emit('notification', {
            'type': 'booking_confirmation',
            'customer_id': booking_data.get('customer_id'),
            'content': 'Vé của bạn đã được đặt thành công!'
        })
        
        # TODO: Send actual email using your email service
        print(f"Email would be sent: {email_content}")
        
    except Exception as e:
        print(f"Error processing booking notification: {e}")

async def process_payment_notification(message):
    try:
        payment_data = json.loads(message['Body'])
        
        # Tạo nội dung thông báo chi tiết hơn
        content = payment_data.get('content', '')
        if not content:
            # Nếu không có nội dung được cung cấp, tạo nội dung mặc định
            amount = payment_data.get('amount', 0)
            formatted_amount = f"{amount:,.0f} VND" if amount else "0 VND"
            content = f"Thanh toán của bạn với số tiền {formatted_amount} đã được xử lý thành công!"
        
        # Process payment notification
        notification = {
            "type": "payment_confirmation",
            "customer_id": payment_data.get('customer_id'),
            "payment_id": payment_data.get('_id'),
            "booking_id": payment_data.get('booking_id'),
            "content": content,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        await db.notifications.insert_one(notification)
        
        # Send real-time notification through Socket.IO
        await sio.emit('notification', {
            'type': 'payment_confirmation',
            'customer_id': payment_data.get('customer_id'), 
            'content': content
        }, room=f"customer_{payment_data.get('customer_id')}")
        
    except Exception as e:
        print(f"Error processing payment notification: {e}")

# Background task to process SQS messages
async def process_sqs_messages():
    while True:
        try:
            # Tăng thời gian sleep giữa các lần poll SQS
            await asyncio.sleep(5)  # Chờ 5 giây thay vì 1 giây
            
            # Giới hạn số lượng message xử lý mỗi lần
            booking_messages = await receive_sqs_messages(BOOKING_CREATED_QUEUE_URL)
            payment_messages = await receive_sqs_messages(PAYMENT_PROCESSED_QUEUE_URL)
            
            # Xử lý message trong batch để giảm tải
            if booking_messages:
                await asyncio.gather(*[process_booking_notification(message) for message in booking_messages[:5]])
                for message in booking_messages[:5]:
                    await delete_sqs_message(BOOKING_CREATED_QUEUE_URL, message['ReceiptHandle'])
            
            if payment_messages:
                await asyncio.gather(*[process_payment_notification(message) for message in payment_messages[:5]])
                for message in payment_messages[:5]:
                    await delete_sqs_message(PAYMENT_PROCESSED_QUEUE_URL, message['ReceiptHandle'])
                    
        except Exception as e:
            print(f"Error in SQS message processing: {e}")
            await asyncio.sleep(10)  # Tăng thời gian sleep khi có lỗi

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")

@sio.event
async def join_room(sid, data):
    if 'customer_id' in data:
        customer_id = data['customer_id']
        await sio.enter_room(sid, f"customer_{customer_id}")
        print(f"Client {sid} joined room for customer {customer_id}")

# Routes
@app.post("/notifications")
async def create_notification(notification: Notification):
    notification_dict = notification.dict()
    notification_dict["created_at"] = datetime.utcnow()
    
    result = await db.notifications.insert_one(notification_dict)
    notification_dict["_id"] = str(result.inserted_id)
    
    # Emit real-time notification
    await sio.emit('notification', {
        'type': notification.type,
        'customer_id': notification.customer_id,
        'content': notification.content
    }, room=f"customer_{notification.customer_id}")
    
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

# Sử dụng socket_app thay vì app
if __name__ == "__main__":
    uvicorn.run(socket_app, host="0.0.0.0", port=8007) 