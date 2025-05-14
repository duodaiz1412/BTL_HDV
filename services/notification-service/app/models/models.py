"""
Định nghĩa các model cho notification service.
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class NotificationBase(BaseModel):
    type: str
    customer_id: str
    content: str
    status: str = "pending"
    booking_id: Optional[str] = None
    payment_id: Optional[str] = None

class NotificationCreate(NotificationBase):
    pass

class NotificationUpdate(BaseModel):
    status: str

class NotificationResponse(NotificationBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True

class Notification(NotificationBase):
    """
    Đây là model để tương thích với code cũ
    """
    pass 