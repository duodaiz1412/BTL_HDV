import json
from fastapi import APIRouter, HTTPException, Depends
from app.models.pydantic_models import BookingRequest
from app.services.service_client import call_service
from app.config.settings import BOOKING_SERVICE_URL, SEAT_SERVICE_URL, MOVIE_SERVICE_URL, NOTIFICATION_SERVICE_URL
from app.sockets.socket_manager import send_notification_to_customer
from app.utils.logger import logger
import httpx

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("/")
async def create_booking(booking: BookingRequest):
    """Tạo một booking mới"""
    # Kiểm tra tính khả dụng của từng ghế theo seat_id
    for seat in booking.seats:
        try:
            seat_data = await call_service(
                f"{SEAT_SERVICE_URL}/seats/{seat.seat_id}",
                error_message=f"Ghế có ID {seat.seat_id} không tồn tại"
            )
            
            if seat_data.get("status") != "available" or seat_data.get("showtime_id") != booking.showtime_id:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Ghế có ID {seat.seat_id} không khả dụng hoặc không thuộc suất chiếu này"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến seat service: {str(e)}")
    
    # Tạo booking
    booking_result = await call_service(
        f"{BOOKING_SERVICE_URL}/bookings",
        method="POST",
        data=booking.dict(),
        error_message="Error creating booking"
    )
    
    # Nếu tạo booking thành công, gửi thông báo
    try:
        # Lấy thông tin chi tiết về phim
        movie_data = await call_service(
            f"{MOVIE_SERVICE_URL}/movies/{booking.movie_id}",
            error_message="Error getting movie details"
        )
        movie_title = movie_data.get("title", "")
        
        # Lấy ra danh sách seat_number từ seats
        seat_numbers = [seat.seat_number for seat in booking.seats]
        seats_str = ", ".join(seat_numbers)
        formatted_amount = f"{booking.total_amount:,.0f} VND"
        
        # Tạo nội dung thông báo
        notification_content = f"Đặt vé thành công! Vé xem phim '{movie_title}' (ghế {seats_str}) với số tiền {formatted_amount}. Vui lòng thanh toán trong vòng 15 phút."
        
        # Tạo thông báo
        notification_data = {
            "type": "booking_confirmation",
            "customer_id": booking.customer_id,
            "content": notification_content,
            "booking_id": booking_result.get("_id", "")
        }
        
        # Gửi thông báo đến notification service và socket
        notification_result = await call_service(
            f"{NOTIFICATION_SERVICE_URL}/notifications",
            method="POST",
            data=notification_data,
            timeout=10.0,
            error_message="Error creating notification"
        )
        
        success = await send_notification_to_customer(booking.customer_id, notification_result)
        if success:
            logger.info(f"Successfully sent booking notification to customer {booking.customer_id}")
        else:
            logger.error(f"Failed to send booking notification to customer {booking.customer_id}")
    except Exception as notification_error:
        # Chỉ ghi log lỗi thông báo, không ảnh hưởng đến booking
        logger.error(f"Error sending notification: {notification_error}")
    
    return booking_result

@router.get("/{booking_id}")
async def get_booking(booking_id: str):
    """Lấy thông tin chi tiết một booking"""
    return await call_service(
        f"{BOOKING_SERVICE_URL}/bookings/{booking_id}",
        error_message="Error getting booking"
    )

@router.get("/customer/{customer_id}")
async def get_customer_bookings(customer_id: str):
    """Lấy danh sách booking của một khách hàng"""
    return await call_service(
        f"{BOOKING_SERVICE_URL}/bookings/customer/{customer_id}",
        error_message="Error getting customer bookings"
    ) 