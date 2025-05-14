import json
from fastapi import APIRouter, HTTPException
from app.models.pydantic_models import PaymentRequest
from app.services.service_client import call_service
from app.config.settings import PAYMENT_SERVICE_URL, BOOKING_SERVICE_URL, SEAT_SERVICE_URL, NOTIFICATION_SERVICE_URL
from app.sockets.socket_manager import send_notification_to_customer
from app.utils.logger import logger

router = APIRouter(prefix="/payments", tags=["payments"])

@router.post("/")
async def create_payment(payment: PaymentRequest):
    """Tạo một payment mới"""
    # Kiểm tra booking tồn tại
    booking_data = await call_service(
        f"{BOOKING_SERVICE_URL}/bookings/{payment.booking_id}",
        error_message="Booking not found"
    )
    
    # Tạo payment
    payment_result = await call_service(
        f"{PAYMENT_SERVICE_URL}/payments",
        method="POST",
        data=payment.dict(),
        timeout=30.0,
        error_message="Error creating payment"
    )
    
    # Cập nhật trạng thái booking
    await call_service(
        f"{BOOKING_SERVICE_URL}/bookings/{payment.booking_id}/status",
        method="PUT",
        params={"status": "paid"},
        error_message="Error updating booking status"
    )
    
    # Cập nhật trạng thái các ghế thành paid
    booking_seats = booking_data.get("seats", [])
    for seat in booking_seats:
        try:
            await call_service(
                f"{SEAT_SERVICE_URL}/seats/{seat.get('seat_id')}/status",
                method="PUT",
                data={"status": "paid"},
                error_message=f"Error updating seat status for seat {seat.get('seat_id')}"
            )
        except Exception as seat_error:
            logger.error(f"Error updating seat status: {seat_error}")
    
    # Tạo và gửi thông báo thanh toán thành công
    try:
        movie_title = booking_data.get("movie_title", "")
        # Lấy ra danh sách seat_number từ seats
        seat_numbers = [seat.get('seat_number') for seat in booking_seats]
        seats_str = ", ".join(seat_numbers)
        formatted_amount = f"{payment.amount:,.0f} VND"
        
        # Tạo nội dung thông báo
        notification_content = f"Thanh toán thành công! Vé xem phim '{movie_title}' (ghế {seats_str}) với số tiền {formatted_amount} đã được xác nhận."
        
        # Tạo thông báo
        notification_data = {
            "type": "payment_confirmation",
            "customer_id": booking_data.get("customer_id"),
            "content": notification_content,
            "booking_id": payment.booking_id,
            "payment_id": payment_result.get("_id", "")
        }
        
        # Gửi thông báo đến notification service
        notification_result = await call_service(
            f"{NOTIFICATION_SERVICE_URL}/notifications",
            method="POST",
            data=notification_data,
            timeout=10.0,
            error_message="Error creating notification"
        )
        
        # Gửi thông báo qua websocket
        customer_id = booking_data.get("customer_id")
        if customer_id:
            success = await send_notification_to_customer(customer_id, notification_result)
            if success:
                logger.info(f"Successfully sent payment notification to customer {customer_id}")
            else:
                logger.error(f"Failed to send payment notification to customer {customer_id}")
                
    except Exception as notification_error:
        # Chỉ ghi log lỗi thông báo, không ảnh hưởng đến thanh toán
        logger.error(f"Error sending notification: {notification_error}")
    
    return payment_result

@router.get("/{payment_id}")
async def get_payment(payment_id: str):
    """Lấy thông tin chi tiết một payment"""
    return await call_service(
        f"{PAYMENT_SERVICE_URL}/payments/{payment_id}",
        error_message="Error getting payment"
    )

@router.get("/booking/{booking_id}")
async def get_booking_payments(booking_id: str):
    """Lấy danh sách payment của một booking"""
    return await call_service(
        f"{PAYMENT_SERVICE_URL}/payments/booking/{booking_id}",
        error_message="Error getting booking payments"
    ) 