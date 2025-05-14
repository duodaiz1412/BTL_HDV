"""
Admin routes cho notification service.
"""
from fastapi import APIRouter
from typing import Dict, Any
from app.services import toggle_sqs_processing, get_sqs_status, get_active_connections
import logging

logger = logging.getLogger("notification-service")

router = APIRouter(prefix="/admin", tags=["admin"])

@router.put("/sqs/toggle", response_model=Dict[str, Any])
async def toggle_sqs_processing_endpoint(enable: bool):
    """Bật hoặc tắt xử lý hàng đợi SQS."""
    return await toggle_sqs_processing(enable)

@router.get("/sqs/status", response_model=Dict[str, Any])
async def get_sqs_status_endpoint():
    """Lấy trạng thái của xử lý hàng đợi SQS."""
    sqs_status = await get_sqs_status()
    connections = get_active_connections()
    
    # Kết hợp thông tin từ cả hai dịch vụ
    return {**sqs_status, **connections}

@router.get("/health", response_model=Dict[str, str])
async def health_check():
    """Kiểm tra trạng thái hoạt động của service."""
    return {"status": "healthy"} 