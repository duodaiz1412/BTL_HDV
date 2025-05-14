"""
SQS service functions.
"""
import aioboto3
import json
import logging
from datetime import datetime
from app.config.settings import (
    AWS_ACCESS_KEY_ID, 
    AWS_SECRET_ACCESS_KEY, 
    AWS_REGION
)
from app.database.mongodb import create_notification

logger = logging.getLogger("notification-service")

# Session management
sqs_session = None

async def get_sqs_session():
    """Tạo và trả về phiên aioboto3 được chia sẻ"""
    global sqs_session
    if sqs_session is None:
        sqs_session = aioboto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
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

async def process_booking_notification(message):
    """Xử lý thông báo đặt vé"""
    try:
        # Import here to avoid circular imports
        from app.services.socketio_service import send_notification_to_customer
        
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
        result = await create_notification(notification)
        
        # Gửi thông báo qua Socket.IO
        await send_notification_to_customer(booking_data.get('customer_id'), result)
        
    except Exception as e:
        logger.error(f"Error processing booking notification: {e}")

async def process_payment_notification(message):
    """Xử lý thông báo thanh toán"""
    try:
        # Import here to avoid circular imports
        from app.services.socketio_service import send_notification_to_customer
        
        payment_data = json.loads(message['Body'])
        
        # Log payment data để debug
        logger.info(f"Processing payment notification with data: {payment_data}")
        
        # Kiểm tra customer_id
        customer_id = payment_data.get('customer_id')
        if not customer_id:
            logger.error(f"Missing customer_id in payment data: {payment_data}")
            # Thử lấy booking_id để tìm customer_id từ booking
            booking_id = payment_data.get('booking_id')
            if booking_id:
                logger.info(f"Attempting to find customer_id from booking_id: {booking_id}")
                # Đây là nơi bạn có thể thêm code để truy vấn booking service
                # để lấy customer_id từ booking_id
            else:
                logger.error("Cannot process payment notification: Missing both customer_id and booking_id")
                return
        
        # Tạo thông báo
        notification = {
            "type": "payment_confirmation",
            "customer_id": customer_id,
            "payment_id": payment_data.get('_id'),
            "content": f"Payment of {payment_data.get('amount', 0)} has been processed successfully.",
            "status": "pending",
            "created_at": datetime.utcnow()
        }
        result = await create_notification(notification)
        
        # Gửi thông báo qua Socket.IO
        await send_notification_to_customer(customer_id, result)
        
    except Exception as e:
        logger.error(f"Error processing payment notification: {e}")

async def toggle_sqs_processing(enable: bool):
    """Bật hoặc tắt xử lý SQS"""
    # Import here to avoid circular imports
    import app.services.queue_processor as queue_processor
    queue_processor.ENABLE_SQS_PROCESSING = enable
    return {"message": f"SQS processing {'enabled' if enable else 'disabled'}", "status": enable}

async def get_sqs_status():
    """Lấy trạng thái xử lý SQS"""
    # Import here to avoid circular imports
    from app.services.queue_processor import ENABLE_SQS_PROCESSING, sqs_tasks
    
    task_statuses = {}
    for i, task in enumerate(sqs_tasks):
        task_statuses[f"task_{i}"] = {
            "done": task.done(),
            "cancelled": task.cancelled() if task.done() else False,
            "exception": str(task.exception()) if task.done() and not task.cancelled() and task.exception() else None
        }
    
    return {
        "sqs_processing_enabled": ENABLE_SQS_PROCESSING,
        "tasks": task_statuses
    } 