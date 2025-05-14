from typing import List, Optional
from pydantic import BaseModel, EmailStr

class SeatInfo(BaseModel):
    seat_id: str
    seat_number: str

class BookingRequest(BaseModel):
    customer_id: str
    movie_id: str
    showtime_id: str
    showtime: str
    seats: List[SeatInfo]  # Danh sách các seat chứa cả seat_id và seat_number
    total_amount: float
    status: str = "pending"

class PaymentRequest(BaseModel):
    booking_id: str
    amount: float
    payment_method: str
    status: str = "pending"

class CreateShowtimesRequest(BaseModel):
    movie_id: str
    duration: int  # Thời lượng phim (phút)
    date: str  # Ngày muốn tạo showtimes (format: YYYY-MM-DD)
    theater: str = "Beta Cinema"  # Rạp chiếu phim mặc định
    price: float = 100000  # Giá vé mặc định (VND)
    
class ShowtimeResponse(BaseModel):
    id: str
    movie_id: str
    start_time: str
    end_time: str
    date: str 