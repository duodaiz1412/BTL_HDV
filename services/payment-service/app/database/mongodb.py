from motor.motor_asyncio import AsyncIOMotorClient
import os
from bson import ObjectId
from typing import Dict, Any, List

class Database:
    client: AsyncIOMotorClient = None
    db = None

    @classmethod
    async def connect_to_mongodb(cls):
        """Kết nối đến MongoDB."""
        mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        cls.client = AsyncIOMotorClient(mongodb_uri)
        cls.db = cls.client.payment_db
        return cls.client

    @classmethod
    async def close_mongodb_connection(cls):
        """Đóng kết nối MongoDB."""
        if cls.client:
            cls.client.close()

    @classmethod
    def convert_mongo_id(cls, document: Dict[str, Any]) -> Dict[str, Any]:
        """Chuyển đổi _id từ ObjectId sang string."""
        if document:
            document["id"] = str(document.pop("_id"))
            return document
        return None
    
    @classmethod
    async def create_payment(cls, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo một payment mới trong database."""
        result = await cls.db.payments.insert_one(payment_data)
        payment_data["_id"] = result.inserted_id
        return cls.convert_mongo_id(payment_data)
    
    @classmethod
    async def get_payment(cls, payment_id: str) -> Dict[str, Any]:
        """Lấy payment theo ID."""
        payment = await cls.db.payments.find_one({"_id": ObjectId(payment_id)})
        return cls.convert_mongo_id(payment) if payment else None
    
    @classmethod
    async def get_booking_payments(cls, booking_id: str) -> List[Dict[str, Any]]:
        """Lấy danh sách payment theo booking_id."""
        payments = await cls.db.payments.find({"booking_id": booking_id}).to_list(length=None)
        return [cls.convert_mongo_id(payment) for payment in payments]
    
    @classmethod
    async def update_payment_status(cls, payment_id: str, status: str) -> bool:
        """Cập nhật trạng thái của payment."""
        result = await cls.db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {"status": status}}
        )
        return result.modified_count > 0
    
    @classmethod
    async def refund_payment(cls, payment_id: str, refund_id: str) -> bool:
        """Cập nhật payment thành đã hoàn tiền."""
        result = await cls.db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {
                "$set": {
                    "status": "refunded",
                    "refund_id": refund_id
                }
            }
        )
        return result.modified_count > 0 