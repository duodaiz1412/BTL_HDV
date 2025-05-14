from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException
from app.models.pydantic_models import CreateShowtimesRequest
from app.services.service_client import call_service
from app.config.settings import MOVIE_SERVICE_URL, SEAT_SERVICE_URL
from app.utils.logger import logger

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/showtimes/create-daily")
async def create_daily_showtimes(request: CreateShowtimesRequest):
    """
    Tạo các suất chiếu tự động cho một ngày dựa trên thời lượng phim
    Mỗi suất chiếu cách nhau 10 phút, bắt đầu từ 6:00 sáng và kết thúc lúc 23:30
    
    Parameters:
    - movie_id: ID của phim
    - duration: Thời lượng phim (phút)
    - date: Ngày muốn tạo suất chiếu (format: YYYY-MM-DD)
    - theater: Rạp chiếu phim (mặc định: "Beta Cinema")
    - price: Giá vé (VND, mặc định: 100000)
    
    Lưu ý: Dữ liệu sẽ được lưu trữ trong MongoDB Atlas
    """
    try:
        # Chuyển đổi định dạng ngày
        date = request.date
        movie_id = request.movie_id
        duration = request.duration  # Thời lượng phim (phút)
        
        # Thời gian bắt đầu và kết thúc của rạp
        start_time = datetime.strptime(f"{date} 06:00:00", "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(f"{date} 23:30:00", "%Y-%m-%d %H:%M:%S")
        
        # Thời gian giữa các suất chiếu (phút)
        time_between_showtimes = 10  # Phút
        
        showtimes = []
        current_time = start_time
        
        # Lấy thông tin phim từ Movie Service để xác nhận phim tồn tại
        movie_data = await call_service(
            f"{MOVIE_SERVICE_URL}/movies/{movie_id}",
            error_message=f"Không tìm thấy phim với ID {movie_id}"
        )
        
        # Tạo các suất chiếu
        while current_time <= end_time:
            # Thời gian kết thúc của suất chiếu = thời gian bắt đầu + thời lượng phim
            showtime_end = current_time + timedelta(minutes=duration)
            
            # Nếu thời gian kết thúc vượt quá thời gian đóng cửa rạp, dừng vòng lặp
            if showtime_end > end_time:
                break
            
            # Tạo showtime mới
            showtime_data = {
                "movie_id": movie_id,
                "start_time": current_time.strftime("%H:%M"),
                "end_time": showtime_end.strftime("%H:%M"),
                "date": date,
                "movie_title": movie_data.get("title", ""),
                "theater": request.theater,
                "price": request.price,
                "time": current_time.isoformat()  # Sử dụng ISO format cho datetime
            }
            
            # Gửi request tạo showtime đến Movie Service
            try:
                created_showtime = await call_service(
                    f"{MOVIE_SERVICE_URL}/showtimes",
                    method="POST",
                    data=showtime_data,
                    error_message=f"Lỗi khi tạo suất chiếu lúc {current_time.strftime('%H:%M')}"
                )
                showtimes.append(created_showtime)
            except Exception as e:
                logger.error(f"Lỗi khi tạo suất chiếu lúc {current_time.strftime('%H:%M')}: {str(e)}")
            
            # Cập nhật thời gian cho suất chiếu tiếp theo (thời gian kết thúc + thời gian nghỉ giữa các suất)
            current_time = showtime_end + timedelta(minutes=time_between_showtimes)
        
        return {
            "message": f"Đã tạo {len(showtimes)} suất chiếu cho ngày {date}",
            "showtimes": showtimes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo suất chiếu: {str(e)}")

@router.post("/seats/create-for-showtime/{showtime_id}")
async def create_seats_for_showtime(showtime_id: str):
    """
    Tạo tất cả các ghế từ A1 đến E10 cho một suất chiếu
    
    Lưu ý: Dữ liệu sẽ được lưu trữ trong MongoDB Atlas
    """
    try:
        # Kiểm tra xem showtime có tồn tại không
        await call_service(
            f"{MOVIE_SERVICE_URL}/showtimes/{showtime_id}",
            error_message=f"Không tìm thấy suất chiếu với ID {showtime_id}"
        )
        
        # Gọi API tạo ghế từ Seat Service
        return await call_service(
            f"{SEAT_SERVICE_URL}/seats/create-for-showtime",
            method="POST",
            params={"showtime_id": showtime_id},
            error_message="Lỗi khi tạo ghế"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo ghế: {str(e)}") 