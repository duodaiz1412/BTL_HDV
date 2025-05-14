"""
Routes cho notification API.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from app.models import NotificationCreate, NotificationResponse, NotificationUpdate
from app.database import (
    get_notification_by_id,
    create_notification,
    get_customer_notifications,
    update_notification_status
)
from app.services import send_notification_to_customer
import logging

logger = logging.getLogger("notification-service")

router = APIRouter(tags=["notifications"])

@router.post("/notifications", response_model=Dict[str, Any])
async def create_notification_endpoint(notification: NotificationCreate, background_tasks: BackgroundTasks):
    """Tạo thông báo mới."""
    try:
        notification_dict = notification.dict()
        
        # Lưu thông báo vào DB
        result = await create_notification(notification_dict)
        
        # Gửi thông báo qua Socket.IO
        background_tasks.add_task(
            send_notification_to_customer,
            notification.customer_id,
            result
        )
        
        return result
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/notifications/{notification_id}", response_model=Dict[str, Any])
async def get_notification_endpoint(notification_id: str):
    """Lấy thông tin chi tiết của một thông báo."""
    try:
        notification = await get_notification_by_id(notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving notification: {e}")
        raise HTTPException(status_code=400, detail="Invalid notification ID format")

@router.get("/notifications/customer/{customer_id}", response_model=List[Dict[str, Any]])
async def get_customer_notifications_endpoint(customer_id: str):
    """Lấy tất cả thông báo của một khách hàng."""
    try:
        return await get_customer_notifications(customer_id)
    except Exception as e:
        logger.error(f"Error retrieving customer notifications: {e}")
        return []

@router.put("/notifications/{notification_id}/status", response_model=Dict[str, str])
async def update_notification_status_endpoint(notification_id: str, notification: NotificationUpdate, background_tasks: BackgroundTasks):
    """Cập nhật trạng thái của thông báo."""
    try:
        # Đưa việc cập nhật DB ra background task
        background_tasks.add_task(
            update_notification_status,
            notification_id,
            notification.status
        )
        return {"message": "Notification status update scheduled"}
    except Exception as e:
        logger.error(f"Error updating notification status: {e}")
        raise HTTPException(status_code=400, detail="Invalid notification ID format") 