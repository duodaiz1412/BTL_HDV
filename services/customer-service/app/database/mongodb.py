from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import MONGODB_URI
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger("customer-service")

client = AsyncIOMotorClient(MONGODB_URI)
db = client.customer_db

def convert_mongo_id(customer):
    """Convert MongoDB ObjectId to string."""
    if customer:
        customer["id"] = str(customer.pop("_id"))
        # Không gửi mật khẩu đến client
        if "password" in customer:
            del customer["password"]
    return customer

async def get_customer_by_id(customer_id: str):
    """Get a customer by ID."""
    try:
        customer = await db.customers.find_one({"_id": ObjectId(customer_id)})
        if customer:
            return convert_mongo_id(customer)
        return None
    except Exception as e:
        logger.error(f"Error retrieving customer by ID: {e}")
        return None

async def get_customer_by_email(email: str):
    """Get a customer by email."""
    try:
        customer = await db.customers.find_one({"email": email})
        return customer  # Không convert ID vì cần giữ lại password để verify
    except Exception as e:
        logger.error(f"Error retrieving customer by email: {e}")
        return None

async def create_customer(customer_data: dict):
    """Create a new customer."""
    try:
        customer_data["created_at"] = datetime.now()
        result = await db.customers.insert_one(customer_data)
        customer_data["_id"] = result.inserted_id
        return convert_mongo_id(customer_data)
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise e

async def update_customer(customer_id: str, customer_data: dict):
    """Update a customer."""
    try:
        # Chỉ cập nhật các field có giá trị
        update_data = {k: v for k, v in customer_data.items() if v is not None}
        
        result = await db.customers.update_one(
            {"_id": ObjectId(customer_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    except Exception as e:
        logger.error(f"Error updating customer: {e}")
        return False

async def delete_customer(customer_id: str):
    """Delete a customer."""
    try:
        result = await db.customers.delete_one({"_id": ObjectId(customer_id)})
        return result.deleted_count > 0
    except Exception as e:
        logger.error(f"Error deleting customer: {e}")
        return False 