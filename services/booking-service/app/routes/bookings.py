from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, List
from app.models import BookingBase, BookingResponse
from app.database import (
    get_booking_by_id, 
    get_bookings_by_customer,
    create_booking,
    update_booking_status
)
from app.services import (
    send_booking_created_message,
    send_seats_booked_message,
    update_multiple_seats
)
from app.utils.datetime_utils import get_utc_now, get_hanoi_now, convert_to_hanoi_timezone
import logging

logger = logging.getLogger("booking-service")

router = APIRouter(prefix="/bookings", tags=["bookings"])

@router.post("", response_model=Dict[str, Any])
async def create_booking_endpoint(booking: BookingBase, background_tasks: BackgroundTasks):
    try:
        # Create booking in MongoDB
        booking_dict = booking.dict()
        booking_result = await create_booking(booking_dict)
        
        # Send message to SQS in background task
        background_tasks.add_task(send_booking_created_message, booking_result)
        
        # Update seat status in background task
        background_tasks.add_task(update_multiple_seats, booking.seats, "pending")
        
        return booking_result
    except Exception as e:
        logger.error(f"Error creating booking: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{booking_id}", response_model=Dict[str, Any])
async def get_booking_endpoint(booking_id: str):
    try:
        booking = await get_booking_by_id(booking_id)
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found")
        return booking
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving booking: {e}")
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

@router.get("/customer/{customer_id}", response_model=List[Dict[str, Any]])
async def get_customer_bookings_endpoint(customer_id: str):
    try:
        bookings = await get_bookings_by_customer(customer_id)
        return bookings
    except Exception as e:
        logger.error(f"Error retrieving customer bookings: {e}")
        return []

@router.put("/{booking_id}/status", response_model=Dict[str, str])
async def update_booking_status_endpoint(booking_id: str, status: str, background_tasks: BackgroundTasks):
    try:
        success = await update_booking_status(booking_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Nếu status là confirmed, gửi thông báo đến SQS
        if status == "confirmed":
            booking = await get_booking_by_id(booking_id)
            if booking:
                background_tasks.add_task(send_seats_booked_message, booking)
        
        return {"message": "Booking status updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating booking status: {e}")
        raise HTTPException(status_code=400, detail="Invalid booking ID format")

@router.get("/time")
async def get_server_time():
    """Lấy thời gian hiện tại của server với thông tin múi giờ"""
    utc_now = get_utc_now()
    hanoi_now = get_hanoi_now()
    
    return {
        "utc_time": utc_now.isoformat(),
        "hanoi_time": hanoi_now.isoformat(),
        "timezone": "Asia/Ho_Chi_Minh",
        "utc_offset": "+07:00"
    } 