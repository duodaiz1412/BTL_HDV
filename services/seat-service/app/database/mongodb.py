from bson import ObjectId
from fastapi import HTTPException
from app.database import db

def convert_mongo_id(item):
    """Chuyển đổi ObjectId thành chuỗi để có thể serialize thành JSON"""
    if item and "_id" in item:
        item["_id"] = str(item["_id"])
    return item

async def get_seat_by_id(seat_id: str):
    """Lấy thông tin ghế theo ID"""
    try:
        seat = await db.seats.find_one({"_id": ObjectId(seat_id)})
        if not seat:
            raise HTTPException(status_code=404, detail="Seat not found")
        return convert_mongo_id(seat)
    except:
        raise HTTPException(status_code=400, detail="Invalid seat ID format")

async def get_showtime_seats(showtime_id: str):
    """Lấy danh sách ghế của một suất chiếu"""
    seats = await db.seats.find({"showtime_id": showtime_id}).to_list(length=None)
    return [convert_mongo_id(seat) for seat in seats]

async def update_seat_status(seat_id: str, status: str):
    """Cập nhật trạng thái của ghế"""
    try:
        result = await db.seats.update_one(
            {"_id": ObjectId(seat_id)},
            {"$set": {"status": status}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Seat not found")
        return {"message": "Seat status updated successfully"}
    except:
        raise HTTPException(status_code=400, detail="Invalid seat ID format")

async def check_seats_availability(showtime_id: str, seats: list):
    """Kiểm tra tình trạng sẵn có của các ghế"""
    for seat_number in seats:
        seat = await db.seats.find_one({
            "showtime_id": showtime_id,
            "seat_number": seat_number,
            "status": "available"
        })
        if not seat:
            raise HTTPException(status_code=400, detail=f"Seat {seat_number} is not available")
    return True

async def book_seats(showtime_id: str, seats: list):
    """Đặt các ghế theo danh sách"""
    from datetime import datetime
    
    result = await db.seats.update_many(
        {
            "showtime_id": showtime_id,
            "seat_number": {"$in": seats}
        },
        {"$set": {"status": "booked", "booked_at": datetime.utcnow()}}
    )
    
    if result.modified_count != len(seats):
        raise HTTPException(status_code=500, detail="Failed to book all seats")
    
    return True

async def release_seats(showtime_id: str, seats: list):
    """Giải phóng các ghế đã đặt"""
    result = await db.seats.update_many(
        {
            "showtime_id": showtime_id,
            "seat_number": {"$in": seats}
        },
        {
            "$set": {
                "status": "available",
                "booking_id": None
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=400, detail="Failed to release seats")
    
    return True 