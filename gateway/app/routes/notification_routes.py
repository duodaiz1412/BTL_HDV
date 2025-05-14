from fastapi import APIRouter, HTTPException
from app.services.service_client import call_service
from app.config.settings import NOTIFICATION_SERVICE_URL
from app.sockets.socket_manager import send_notification_to_customer
from app.utils.logger import logger

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.post("/")
async def create_notification(notification: dict):
    """Tạo một thông báo mới"""
    notification_data = await call_service(
        f"{NOTIFICATION_SERVICE_URL}/notifications",
        method="POST",
        data=notification,
        timeout=10.0,
        error_message="Error creating notification"
    )
    
    # Sau khi tạo thông báo thành công, gửi thông báo qua websocket
    customer_id = notification.get("customer_id")
    if customer_id:
        success = await send_notification_to_customer(customer_id, notification_data)
        if success:
            logger.info(f"Successfully sent notification to customer {customer_id}")
        else:
            logger.error(f"Failed to send notification to customer {customer_id}")
    
    return notification_data

@router.get("/{notification_id}")
async def get_notification(notification_id: str):
    """Lấy thông tin chi tiết một thông báo"""
    return await call_service(
        f"{NOTIFICATION_SERVICE_URL}/notifications/{notification_id}",
        timeout=10.0,
        error_message="Error getting notification"
    )

@router.get("/customer/{customer_id}")
async def get_customer_notifications(customer_id: str):
    """Lấy danh sách thông báo của một khách hàng"""
    return await call_service(
        f"{NOTIFICATION_SERVICE_URL}/notifications/customer/{customer_id}",
        timeout=10.0,
        error_message="Error getting customer notifications"
    )

@router.put("/{notification_id}/status")
async def update_notification_status(notification_id: str, status: str):
    """Cập nhật trạng thái thông báo"""
    return await call_service(
        f"{NOTIFICATION_SERVICE_URL}/notifications/{notification_id}/status",
        method="PUT",
        params={"status": status},
        timeout=10.0,
        error_message="Error updating notification status"
    ) 