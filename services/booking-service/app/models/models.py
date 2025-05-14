from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class SeatInfo(BaseModel):
    seat_id: str
    seat_number: str

class BookingBase(BaseModel):
    customer_id: str
    movie_id: str
    showtime_id: str
    showtime: str
    seats: List[SeatInfo]
    total_amount: float
    status: str = "pending"

class BookingCreate(BookingBase):
    pass

class BookingResponse(BookingBase):
    id: str
    created_at: str

class StatusUpdate(BaseModel):
    status: str 