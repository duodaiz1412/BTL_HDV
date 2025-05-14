"""
Database functions cho notification service.
"""
from app.database.mongodb import (
    convert_mongo_id,
    get_notification_by_id,
    get_customer_notifications,
    create_notification,
    update_notification_status
) 