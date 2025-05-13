from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
from dotenv import load_dotenv
import boto3
import aioboto3
from botocore.exceptions import ClientError
import json
import aiohttp
from bson import ObjectId
import asyncio
import logging
from contextlib import asynccontextmanager
import uuid
import socketio

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("notification-service")

load_dotenv()

# Khởi tạo Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:3000', 'http://localhost:8000', '*'],  # Cho phép frontend và API Gateway kết nối
    logger=True,
    engineio_logger=True,
    ping_timeout=60,  # Tăng timeout
    ping_interval=25,  # Đảm bảo ping định kỳ
    always_connect=True,  # Luôn chấp nhận kết nối
)

# SQS Queue URLs
BOOKING_CREATED_QUEUE_URL = os.getenv('SQS_BOOKING_CREATED_URL')
PAYMENT_PROCESSED_QUEUE_URL = os.getenv('SQS_PAYMENT_PROCESSED_URL')

# Biến điều khiển để bật/tắt xử lý SQS
ENABLE_SQS_PROCESSING = True  # Tạm thời tắt xử lý SQS

# Task và session management
sqs_tasks = []
sqs_session = None

# Mapping giữa customer_id và socket session
connected_customers = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo các kết nối khi ứng dụng bắt đầu
    await startup()
    yield
    # Đóng các kết nối khi ứng dụng kết thúc
    await shutdown()

# Khởi tạo FastAPI app
app = FastAPI(title="Notification Service", lifespan=lifespan)

# Tích hợp Socket.IO với FastAPI
socket_app = socketio.ASGIApp(sio, app)
app.mount("/socket.io", socket_app)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường production nên giới hạn các origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI")
client = AsyncIOMotorClient(MONGODB_URI)
db = client.notification_db

# Models
class Notification(BaseModel):
    type: str
    customer_id: str
    content: str
    status: str = "pending"
    booking_id: Optional[str] = None
    payment_id: Optional[str] = None

# Helper functions
def convert_mongo_id(notification):
    notification["_id"] = str(notification["_id"])
    return notification

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

async def receive_sqs_messages(queue_url):
    """Nhận tin nhắn từ SQS queue sử dụng aioboto3 để tránh chặn event loop"""
    try:
        session = await get_sqs_session()
        async with session.client('sqs') as sqs_client:
            response = await sqs_client.receive_message(
            QueueUrl=queue_url,
            MaxNumberOfMessages=10,
                WaitTimeSeconds=5,
                AttributeNames=['All'],
                MessageAttributeNames=['All']
        )
            messages = response.get('Messages', [])
            logger.info(f"Nhận được {len(messages)} tin nhắn từ queue: {queue_url}")
            return messages
    except Exception as e:
        logger.error(f"Error receiving messages from SQS: {e}")
        return []

async def delete_sqs_message(message):
    """Xóa tin nhắn từ queue sau khi xử lý thành công"""
    try:
        session = await get_sqs_session()
        async with session.client('sqs') as sqs_client:
            await sqs_client.delete_message(
                QueueUrl=message['queue_url'],
                ReceiptHandle=message['ReceiptHandle']
            )
            logger.info(f"Tin nhắn đã được xóa khỏi queue: {message['queue_url']}")
    except Exception as e:
        logger.error(f"Error deleting message from SQS: {e}")

async def send_notification_to_customer(customer_id: str, notification: Dict[str, Any]):
    """Gửi thông báo tới khách hàng thông qua Socket.IO"""
    try:
        # Kiểm tra xem customer_id có trong danh sách kết nối không
        if customer_id in connected_customers:
            for sid in connected_customers[customer_id]:
                # Gửi thông báo tới tất cả các session của customer
                await sio.emit('notification', notification, room=sid)
                logger.info(f"Notification sent to customer {customer_id}, session {sid}")
        else:
            logger.info(f"No active connections for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error sending notification via Socket.IO: {e}")

async def process_booking_notification(message):
    try:
        booking_data = json.loads(message['Body'])
        
        # Tạo nội dung thông báo
        content = f"Đặt vé thành công cho phim {booking_data.get('movie_title', 'Movie')} lúc {booking_data.get('showtime', 'Showtime')}. Ghế: {booking_data.get('seats', [])}. Tổng tiền: {booking_data.get('total_amount', 0)}"
        
        # Store notification in MongoDB
        notification = {
            "type": "booking_confirmation",
            "customer_id": booking_data.get('customer_id'),
            "booking_id": booking_data.get('_id'),
            "content": content,
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        result = await db.notifications.insert_one(notification)
        
        # Thêm _id vào notification
        notification["_id"] = str(result.inserted_id)
        
        # Gửi thông báo qua Socket.IO
        await send_notification_to_customer(booking_data.get('customer_id'), notification)
        
    except Exception as e:
        logger.error(f"Error processing booking notification: {e}")

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
        result = await db.notifications.insert_one(notification)
        
        # Thêm _id vào notification
        notification["_id"] = str(result.inserted_id)
        
        # Gửi thông báo qua Socket.IO
        await send_notification_to_customer(payment_data.get('customer_id'), notification)
        
    except Exception as e:
        logger.error(f"Error processing payment notification: {e}")

# Background task để xử lý booking queue
async def process_booking_queue():
    while True:
        try:
            if not ENABLE_SQS_PROCESSING:
                await asyncio.sleep(10)  # Chờ lâu hơn khi SQS bị tắt
                continue
                
            logger.info(f"Đang kiểm tra tin nhắn từ booking queue: {BOOKING_CREATED_QUEUE_URL}")
            messages = await receive_sqs_messages(BOOKING_CREATED_QUEUE_URL)
            for message in messages:
                # Thêm queue_url vào message để sử dụng khi xóa tin nhắn
                message['queue_url'] = BOOKING_CREATED_QUEUE_URL
                try:
                    await process_booking_notification(message)
                    await delete_sqs_message(message)
                except Exception as e:
                    logger.error(f"Lỗi xử lý tin nhắn booking: {e}")
            
            # Ngủ ngắn hơn nếu không có tin nhắn
            await asyncio.sleep(1 if messages else 5)
        except asyncio.CancelledError:
            # Xử lý việc hủy task
            logger.info("Booking queue processor was cancelled")
            break
        except Exception as e:
            logger.error(f"Error in booking queue processing: {e}")
            await asyncio.sleep(5)  # Chờ lâu hơn khi có lỗi

# Background task để xử lý payment queue
async def process_payment_queue():
    while True:
        try:
            if not ENABLE_SQS_PROCESSING:
                await asyncio.sleep(10)  # Chờ lâu hơn khi SQS bị tắt
                continue
            
            logger.info(f"Đang kiểm tra tin nhắn từ payment queue: {PAYMENT_PROCESSED_QUEUE_URL}")
            messages = await receive_sqs_messages(PAYMENT_PROCESSED_QUEUE_URL)
            for message in messages:
                # Thêm queue_url vào message để sử dụng khi xóa tin nhắn
                message['queue_url'] = PAYMENT_PROCESSED_QUEUE_URL
                try:
                    await process_payment_notification(message)
                    await delete_sqs_message(message)
                except Exception as e:
                    logger.error(f"Lỗi xử lý tin nhắn payment: {e}")
            
            # Ngủ ngắn hơn nếu không có tin nhắn
            await asyncio.sleep(1 if messages else 5)
        except asyncio.CancelledError:
            # Xử lý việc hủy task
            logger.info("Payment queue processor was cancelled")
            break
        except Exception as e:
            logger.error(f"Error in payment queue processing: {e}")
            await asyncio.sleep(5)  # Chờ lâu hơn khi có lỗi

# Khởi tạo background tasks
async def startup():
    global sqs_tasks
    # Xóa bất kỳ task nào đang chạy
    for task in sqs_tasks:
        if not task.done():
            task.cancel()
    
    # Tạo các task mới
    booking_task = asyncio.create_task(process_booking_queue())
    payment_task = asyncio.create_task(process_payment_queue())
    sqs_tasks = [booking_task, payment_task]
    logger.info("SQS processing tasks started")

# Dọn dẹp khi shutdown
async def shutdown():
    global sqs_tasks, sqs_session
    # Hủy tất cả task đang chạy
    for task in sqs_tasks:
        if not task.done():
            task.cancel()
    
    # Chờ tất cả task kết thúc
    if sqs_tasks:
        await asyncio.gather(*[task for task in sqs_tasks], return_exceptions=True)
    
    # Đóng session
    if sqs_session:
        sqs_session = None
    
    logger.info("SQS processing cleaned up")

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Xử lý khi client kết nối"""
    logger.info(f"Client kết nối Socket.IO: {sid}")
    await sio.emit('connected', {'status': 'ok', 'sid': sid}, room=sid)

@sio.event
async def disconnect(sid):
    """Xử lý khi client ngắt kết nối"""
    # Tìm và xóa sid khỏi connected_customers
    for customer_id, sessions in list(connected_customers.items()):
        if sid in sessions:
            connected_customers[customer_id].remove(sid)
            logger.info(f"Client {sid} disconnected from customer {customer_id}")
            # Nếu không còn session nào cho customer này, xóa customer khỏi dictionary
            if not connected_customers[customer_id]:
                del connected_customers[customer_id]
                logger.info(f"Removed customer {customer_id} from connected customers")
            break

@sio.event
async def join_room(sid, data):
    """Xử lý khi client tham gia vào phòng của khách hàng"""
    try:
        customer_id = data.get('customer_id')
        if not customer_id:
            await sio.emit('error', {'message': 'Missing customer_id'}, room=sid)
            return
        
        # Thêm sid vào danh sách session của customer
        if customer_id not in connected_customers:
            connected_customers[customer_id] = set()
        connected_customers[customer_id].add(sid)
        
        logger.info(f"Client {sid} joined room for customer {customer_id}")
        await sio.emit('joined', {'status': 'ok', 'customer_id': customer_id}, room=sid)
        
        # Gửi các thông báo chưa đọc
        unread_notifications = await db.notifications.find({
            "customer_id": customer_id,
            "status": "pending"
        }).to_list(length=None)
        
        if unread_notifications:
            # Chuyển đổi _id từ ObjectId sang string
            for notification in unread_notifications:
                notification["_id"] = str(notification["_id"])
                if "created_at" in notification:
                    notification["created_at"] = notification["created_at"].isoformat()
            
            await sio.emit('unread_notifications', unread_notifications, room=sid)
            logger.info(f"Sent {len(unread_notifications)} unread notifications to customer {customer_id}")
    
    except Exception as e:
        logger.error(f"Error in join_room: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def mark_read(sid, data):
    """Xử lý khi client đánh dấu thông báo đã đọc"""
    try:
        notification_id = data.get('notification_id')
        if not notification_id:
            await sio.emit('error', {'message': 'Missing notification_id'}, room=sid)
            return
        
        # Cập nhật trạng thái trong database
        result = await db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"status": "read"}}
        )
        
        if result.modified_count > 0:
            await sio.emit('notification_marked_read', {'notification_id': notification_id}, room=sid)
            logger.info(f"Notification {notification_id} marked as read")
        else:
            await sio.emit('error', {'message': 'Notification not found or already read'}, room=sid)
    
    except Exception as e:
        logger.error(f"Error in mark_read: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

# Routes
@app.post("/notifications", response_model=Dict[str, Any])
async def create_notification(notification: Notification, background_tasks: BackgroundTasks):
    notification_dict = notification.dict()
    notification_dict["created_at"] = datetime.utcnow()
    
    # Lưu thông báo vào DB
    result = await db.notifications.insert_one(notification_dict)
    notification_id = str(result.inserted_id)
    
    # Chuẩn bị thông báo để gửi
    notification_dict["_id"] = notification_id
    
    # Gửi thông báo qua Socket.IO
    background_tasks.add_task(
        send_notification_to_customer,
        notification.customer_id,
        convert_mongo_id(notification_dict)
    )
    
    return convert_mongo_id(notification_dict)

@app.get("/notifications/{notification_id}", response_model=Dict[str, Any])
async def get_notification(notification_id: str):
    try:
        notification = await db.notifications.find_one({"_id": ObjectId(notification_id)})
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return convert_mongo_id(notification)
    except Exception as e:
        logger.error(f"Error retrieving notification: {e}")
        raise HTTPException(status_code=400, detail="Invalid notification ID format")

@app.get("/notifications/customer/{customer_id}", response_model=List[Dict[str, Any]])
async def get_customer_notifications(customer_id: str):
    try:
        notifications = await db.notifications.find({"customer_id": customer_id}).to_list(length=None)
        return [convert_mongo_id(notification) for notification in notifications]
    except Exception as e:
        logger.error(f"Error retrieving customer notifications: {e}")
        return []

@app.put("/notifications/{notification_id}/status", response_model=Dict[str, str])
async def update_notification_status(notification_id: str, status: str, background_tasks: BackgroundTasks):
    try:
        # Đưa việc cập nhật DB ra background task
        background_tasks.add_task(
            db.notifications.update_one,
            {"_id": ObjectId(notification_id)},
            {"$set": {"status": status}}
        )
        return {"message": "Notification status update scheduled"}
    except Exception as e:
        logger.error(f"Error updating notification status: {e}")
        raise HTTPException(status_code=400, detail="Invalid notification ID format")

# API để bật/tắt xử lý SQS
@app.put("/admin/sqs/toggle", response_model=Dict[str, Any])
async def toggle_sqs_processing(enable: bool):
    global ENABLE_SQS_PROCESSING
    ENABLE_SQS_PROCESSING = enable
    
    # Khởi động lại các task nếu cần
    if enable and (not sqs_tasks or all(task.done() for task in sqs_tasks)):
        await startup()
        
    return {"message": f"SQS processing {'enabled' if enable else 'disabled'}", "status": enable}

# API để kiểm tra trạng thái xử lý SQS
@app.get("/admin/sqs/status", response_model=Dict[str, Any])
async def get_sqs_status():
    task_statuses = {}
    for i, task in enumerate(sqs_tasks):
        task_statuses[f"task_{i}"] = {
            "done": task.done(),
            "cancelled": task.cancelled() if task.done() else False,
            "exception": str(task.exception()) if task.done() and not task.cancelled() and task.exception() else None
        }
    
    return {
        "sqs_processing_enabled": ENABLE_SQS_PROCESSING,
        "tasks": task_statuses,
        "active_connections": len(connected_customers),
        "customers_connected": list(connected_customers.keys())
    } 