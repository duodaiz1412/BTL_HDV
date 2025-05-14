import os
from datetime import datetime
from typing import Dict, Any, List
from fastapi import BackgroundTasks
from app.database.mongodb import Database
from app.services.sqs_service import SQSService

PAYMENT_PROCESSED_QUEUE_URL = os.getenv('SQS_PAYMENT_PROCESSED_URL')

class PaymentService:
    @staticmethod
    async def create_payment(payment_data: Dict[str, Any], background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """Tạo một payment mới và gửi thông báo đến SQS."""
        payment_data["created_at"] = datetime.utcnow()
        payment = await Database.create_payment(payment_data)
        
        # Gửi thông báo đến SQS trong background task
        sqs_message = payment.copy()
        sqs_message["created_at"] = sqs_message["created_at"].isoformat()
        background_tasks.add_task(
            SQSService.send_message, 
            PAYMENT_PROCESSED_QUEUE_URL, 
            sqs_message
        )
        
        return payment
    
    @staticmethod
    async def get_payment(payment_id: str) -> Dict[str, Any]:
        """Lấy payment theo ID."""
        return await Database.get_payment(payment_id)
    
    @staticmethod
    async def get_booking_payments(booking_id: str) -> List[Dict[str, Any]]:
        """Lấy danh sách payment theo booking_id."""
        return await Database.get_booking_payments(booking_id)
    
    @staticmethod
    async def update_payment_status(payment_id: str, status: str, background_tasks: BackgroundTasks) -> bool:
        """Cập nhật trạng thái của payment và gửi thông báo đến SQS nếu trạng thái là completed."""
        success = await Database.update_payment_status(payment_id, status)
        
        # Nếu status là completed, gửi thông báo đến SQS
        if success and status == "completed":
            payment = await Database.get_payment(payment_id)
            if payment:
                background_tasks.add_task(
                    SQSService.send_message, 
                    PAYMENT_PROCESSED_QUEUE_URL, 
                    payment
                )
                
        return success
    
    @staticmethod
    async def refund_payment(payment_id: str, background_tasks: BackgroundTasks) -> Dict[str, Any]:
        """Hoàn tiền cho payment và gửi thông báo đến SQS."""
        payment = await Database.get_payment(payment_id)
        if not payment:
            return None
            
        if payment["status"] != "completed":
            return {"error": "Payment is not completed"}
            
        # Tạo refund ID và cập nhật payment
        refund_id = f"REF_{payment_id}"
        success = await Database.refund_payment(payment_id, refund_id)
        
        if success:
            # Gửi thông báo đến SQS
            refund_message = {
                "payment_id": payment_id,
                "booking_id": payment["booking_id"],
                "refund_id": refund_id,
                "status": "refunded",
                "amount": payment.get("amount", 0)
            }
            background_tasks.add_task(
                SQSService.send_message, 
                PAYMENT_PROCESSED_QUEUE_URL, 
                refund_message
            )
            
            return {
                "message": "Payment refunded successfully",
                "refund_id": refund_id
            }
        
        return {"error": "Failed to refund payment"} 