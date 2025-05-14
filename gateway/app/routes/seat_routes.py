from fastapi import APIRouter, HTTPException
from typing import List
from app.services.service_client import call_service
from app.config.settings import SEAT_SERVICE_URL

router = APIRouter(prefix="/seats", tags=["seats"])

@router.get("/")
async def get_all_seats():
    """Lấy danh sách tất cả ghế"""
    return await call_service(
        f"{SEAT_SERVICE_URL}/seats", 
        error_message="Error connecting to seat service"
    )

@router.get("/showtime/{showtime_id}")
async def get_showtime_seats(showtime_id: str):
    """Lấy danh sách ghế của một suất chiếu"""
    return await call_service(
        f"{SEAT_SERVICE_URL}/seats/showtime/{showtime_id}",
        error_message="Error getting seats for showtime"
    )

@router.post("/check")
async def check_seats(showtime_id: str, seats: List[str]):
    """Kiểm tra tính khả dụng của ghế"""
    return await call_service(
        f"{SEAT_SERVICE_URL}/seats/check",
        method="POST",
        data=seats,
        params={"showtime_id": showtime_id},
        error_message="Error checking seat availability"
    ) 