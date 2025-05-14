from fastapi import APIRouter
from typing import Dict, Any, List
from app.database import (
    get_all_showtimes,
    get_all_seats,
    get_all_payments,
    get_all_notifications
)
import logging

logger = logging.getLogger("booking-service")

router = APIRouter(tags=["resources"])

@router.get("/showtimes", response_model=List[Dict[str, Any]])
async def get_showtimes_endpoint():
    showtimes = await get_all_showtimes()
    return showtimes

@router.get("/seats", response_model=List[Dict[str, Any]])
async def get_seats_endpoint():
    seats = await get_all_seats()
    return seats

@router.get("/payments", response_model=List[Dict[str, Any]])
async def get_payments_endpoint():
    payments = await get_all_payments()
    return payments

@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_notifications_endpoint():
    notifications = await get_all_notifications()
    return notifications 