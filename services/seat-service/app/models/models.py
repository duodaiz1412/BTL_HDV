from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class SeatBase(BaseModel):
    showtime_id: str
    seat_number: str
    status: str = "available"
    
class BookingRequest(BaseModel):
    showtime_id: str
    seats: List[str]
    
class SeatStatusUpdate(BaseModel):
    status: str
    
class ShowtimeSeatsInit(BaseModel):
    showtime_id: str
    total_seats: int 