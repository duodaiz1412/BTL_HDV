"""
MongoDB connection và functions.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import MONGODB_URI
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger("notification-service")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.notification_db

def convert_mongo_id(notification):
    """Convert MongoDB ObjectId to string."""
    if notification:
        notification["id"] = str(notification.pop("_id"))
    return notification

async def get_notification_by_id(notification_id: str):
    """Get a notification by ID."""
    try:
        notification = await db.notifications.find_one({"_id": ObjectId(notification_id)})
        if notification:
            return convert_mongo_id(notification)
        return None
    except Exception as e:
        logger.error(f"Error retrieving notification by ID: {e}")
        return None

async def get_customer_notifications(customer_id: str):
    """Get all notifications for a customer."""
    try:
        notifications = await db.notifications.find({"customer_id": customer_id}).to_list(length=None)
        return [convert_mongo_id(notification) for notification in notifications]
    except Exception as e:
        logger.error(f"Error retrieving customer notifications: {e}")
        return []

async def get_unread_customer_notifications(customer_id: str):
    """Get unread notifications for a customer."""
    try:
        notifications = await db.notifications.find({
            "customer_id": customer_id,
            "status": "pending"
        }).to_list(length=None)
        return [convert_mongo_id(notification) for notification in notifications]
    except Exception as e:
        logger.error(f"Error retrieving unread customer notifications: {e}")
        return []

async def create_notification(notification_data: dict):
    """Create a new notification."""
    try:
        notification_data["created_at"] = datetime.utcnow()
        result = await db.notifications.insert_one(notification_data)
        notification_data["_id"] = result.inserted_id
        return convert_mongo_id(notification_data)
    except Exception as e:
        logger.error(f"Error creating notification: {e}")
        raise e

async def update_notification_status(notification_id: str, status: str):
    """Update a notification status."""
    try:
        result = await db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating notification status: {e}")
        return False 