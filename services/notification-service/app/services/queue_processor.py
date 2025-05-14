"""
Queue processing services.
"""
import asyncio
import logging
from app.config.settings import BOOKING_CREATED_QUEUE_URL, PAYMENT_PROCESSED_QUEUE_URL

logger = logging.getLogger("notification-service")

# Task management - định nghĩa biến global ở đây
sqs_tasks = []

# Flag bật/tắt SQS processing
ENABLE_SQS_PROCESSING = True

# Background task để xử lý booking queue
async def process_booking_queue():
    """Xử lý hàng đợi booking"""
    # Import ở đây để tránh circular import
    from app.services.sqs_service import (
        receive_sqs_messages,
        delete_sqs_message,
        process_booking_notification
    )
    
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
    """Xử lý hàng đợi payment"""
    # Import ở đây để tránh circular import
    from app.services.sqs_service import (
        receive_sqs_messages,
        delete_sqs_message,
        process_payment_notification
    )
    
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
    """Khởi tạo các background task"""
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
    """Dọn dẹp tài nguyên khi shutdown"""
    global sqs_tasks
    # Hủy tất cả task đang chạy
    for task in sqs_tasks:
        if not task.done():
            task.cancel()
    
    # Chờ tất cả task kết thúc
    if sqs_tasks:
        await asyncio.gather(*[task for task in sqs_tasks], return_exceptions=True)
    
    # Đóng session (sqs_session không cần thiết ở đây vì đã xử lý trong sqs_service)
    
    logger.info("SQS processing cleaned up") 