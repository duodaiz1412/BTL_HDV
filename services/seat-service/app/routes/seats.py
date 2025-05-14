from fastapi import APIRouter, HTTPException, Depends
from typing import List
from datetime import datetime
from app.models.models import SeatBase, BookingRequest, SeatStatusUpdate, ShowtimeSeatsInit
from app.database.mongodb import (
    convert_mongo_id, get_seat_by_id, get_showtime_seats, 
    update_seat_status, check_seats_availability, 
    book_seats, release_seats
)
from app.database import db
from app.services.sqs_service import send_sqs_message
from app.config.settings import SQS_SEATS_BOOKED_URL
from bson import ObjectId

seats_router = APIRouter(prefix="/seats", tags=["seats"])

@seats_router.post("")
async def create_seat(seat: SeatBase):
    """Tạo một ghế mới"""
    seat_dict = seat.dict()
    seat_dict["created_at"] = datetime.now().isoformat()
    
    result = await db.seats.insert_one(seat_dict)
    seat_dict["id"] = str(result.inserted_id)
    if "_id" in seat_dict:
        del seat_dict["_id"]
    
    return seat_dict

@seats_router.get("/{seat_id}")
async def get_seat(seat_id: str):
    """Lấy thông tin ghế theo ID"""
    return await get_seat_by_id(seat_id)

@seats_router.get("/showtime/{showtime_id}")
async def get_seats_by_showtime(showtime_id: str):
    """Lấy danh sách ghế của một suất chiếu"""
    return await get_showtime_seats(showtime_id)

@seats_router.put("/{seat_id}/status")
async def update_seat_status_endpoint(seat_id: str, status_update: SeatStatusUpdate = None, status: str = None):
    """Cập nhật trạng thái của ghế"""
    # Ưu tiên sử dụng status_update từ body nếu có
    if status_update is not None:
        return await update_seat_status(seat_id, status_update.status)
    # Nếu không có body, sử dụng query parameter
    elif status is not None:
        return await update_seat_status(seat_id, status)
    # Nếu không có cả hai, báo lỗi
    else:
        raise HTTPException(status_code=422, detail="Status is required either in body or as query parameter")

@seats_router.post("/check")
async def check_seats_endpoint(booking: BookingRequest):
    """Kiểm tra tình trạng sẵn có của các ghế"""
    try:
        await check_seats_availability(booking.showtime_id, booking.seats)
        return {"message": "All seats are available"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@seats_router.post("/book")
async def book_seats_endpoint(booking: BookingRequest):
    """Đặt các ghế"""
    try:
        # Kiểm tra ghế có sẵn không
        await check_seats_availability(booking.showtime_id, booking.seats)
        
        # Đặt ghế
        await book_seats(booking.showtime_id, booking.seats)
        
        # Gửi thông báo qua SQS
        await send_sqs_message(SQS_SEATS_BOOKED_URL, {
            "showtime_id": booking.showtime_id,
            "seats": booking.seats,
            "booked_at": datetime.utcnow().isoformat()
        })
        
        return {"message": "Seats booked successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@seats_router.post("/release")
async def release_seats_endpoint(booking: BookingRequest):
    """Giải phóng các ghế đã đặt"""
    try:
        await release_seats(booking.showtime_id, booking.seats)
        return {"message": "Seats released successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@seats_router.get("")
async def get_all_seats():
    """Lấy tất cả các ghế"""
    seats = await db.seats.find().to_list(length=None)
    return [convert_mongo_id(seat) for seat in seats]

@seats_router.post("/initialize")
async def initialize_seats(init_data: ShowtimeSeatsInit):
    """Khởi tạo số lượng ghế cho suất chiếu"""
    try:
        # Tạo ghế cho suất chiếu
        seats = []
        for i in range(1, init_data.total_seats + 1):
            seat = {
                "showtime_id": init_data.showtime_id,
                "seat_number": f"A{i}",
                "status": "available",
                "created_at": datetime.utcnow()
            }
            seats.append(seat)
        
        result = await db.seats.insert_many(seats)
        return {"message": f"Initialized {len(result.inserted_ids)} seats"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@seats_router.post("/create-for-showtime")
async def create_seats_for_showtime(showtime_id: str):
    """Tạo ghế theo mẫu cho suất chiếu"""
    try:
        # Kiểm tra xem đã có ghế cho showtime này chưa
        existing_seats = await db.seats.find({"showtime_id": showtime_id}).to_list(length=None)
        if existing_seats:
            return {"message": f"Seats already exist for showtime {showtime_id}", "seats_count": len(existing_seats)}
        
        # Tạo danh sách các ghế từ A1-E10
        rows = ['A', 'B', 'C', 'D', 'E']
        seats = []
        
        for row in rows:
            for num in range(1, 11):  # 1-10
                seat = {
                    "showtime_id": showtime_id,
                    "seat_number": f"{row}{num}",
                    "status": "available",
                    "created_at": datetime.utcnow()
                }
                seats.append(seat)
        
        # Lưu tất cả ghế vào database
        result = await db.seats.insert_many(seats)
        
        return {
            "message": f"Created {len(result.inserted_ids)} seats for showtime {showtime_id}",
            "seat_count": len(result.inserted_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 