from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, time, timedelta
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

app = FastAPI(title="API Gateway")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service URLs
MOVIE_SERVICE_URL = os.getenv("MOVIE_SERVICE_URL", "http://movie-service:8000")
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://booking-service:8000")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
SEAT_SERVICE_URL = os.getenv("SEAT_SERVICE_URL", "http://seat-service:8000")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")

# Models
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

# Movie Routes
@app.get("/movies")
async def get_movies():
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MOVIE_SERVICE_URL}/movies")
        return response.json()

@app.get("/movies/{movie_id}")
async def get_movie(movie_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MOVIE_SERVICE_URL}/movies/{movie_id}")
        return response.json()

@app.get("/movies/{movie_id}/showtimes")
async def get_movie_showtimes(movie_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MOVIE_SERVICE_URL}/showtimes/movie/{movie_id}")
        return response.json()

# Seat Routes
@app.get("/seats")
async def get_all_seats():
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{SEAT_SERVICE_URL}/seats")
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to seat service: {str(e)}")

@app.get("/seats/showtime/{showtime_id}")
async def get_showtime_seats(showtime_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SEAT_SERVICE_URL}/seats/showtime/{showtime_id}")
        return response.json()

@app.post("/seats/check")
async def check_seats(showtime_id: str, seats: List[str]):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SEAT_SERVICE_URL}/seats/check",
                params={"showtime_id": showtime_id},
                json=seats
            )
            if response.status_code == 400:
                raise HTTPException(status_code=400, detail=response.json()["detail"])
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to seat service: {str(e)}")

# Booking Routes
@app.post("/bookings")
async def create_booking(booking: BookingRequest):
    async with httpx.AsyncClient() as client:
        try:
            # Kiểm tra tính khả dụng của từng ghế theo seat_id
            for seat in booking.seats:
                try:
                    seat_response = await client.get(f"{SEAT_SERVICE_URL}/seats/{seat.seat_id}")
                    if seat_response.status_code != 200:
                        raise HTTPException(status_code=400, detail=f"Ghế có ID {seat.seat_id} không tồn tại")
                    
                    seat_data = seat_response.json()
                    if seat_data.get("status") != "available" or seat_data.get("showtime_id") != booking.showtime_id:
                        raise HTTPException(status_code=400, detail=f"Ghế có ID {seat.seat_id} không khả dụng hoặc không thuộc suất chiếu này")
                except httpx.RequestError as e:
                    raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến seat service: {str(e)}")
            
            # Tạo booking
            response = await client.post(
                f"{BOOKING_SERVICE_URL}/bookings",
                json=booking.dict()
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to service: {str(e)}")

@app.get("/bookings/{booking_id}")
async def get_booking(booking_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BOOKING_SERVICE_URL}/bookings/{booking_id}"
        )
        return response.json()

@app.get("/bookings/customer/{customer_id}")
async def get_customer_bookings(customer_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BOOKING_SERVICE_URL}/bookings/customer/{customer_id}"
        )
        return response.json()

# Payment Routes
@app.post("/payments")
async def create_payment(payment: PaymentRequest):
    async with httpx.AsyncClient(timeout=30.0) as client:  # Tăng timeout lên 30 giây
        try:
            # Kiểm tra booking tồn tại
            booking_response = await client.get(
                f"{BOOKING_SERVICE_URL}/bookings/{payment.booking_id}"
            )
            if booking_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Booking not found")
            
            booking_data = booking_response.json()

            # Tạo payment
            response = await client.post(
                f"{PAYMENT_SERVICE_URL}/payments",
                json=payment.dict()
            )
            
            payment_result = response.json()
            
            if response.status_code == 200:
                # Cập nhật trạng thái booking
                await client.put(
                    f"{BOOKING_SERVICE_URL}/bookings/{payment.booking_id}/status",
                    params={"status": "paid"}
                )
                
                # Cập nhật trạng thái các ghế thành paid
                booking_seats = booking_data.get("seats", [])
                for seat in booking_seats:
                    try:
                        await client.put(
                            f"{SEAT_SERVICE_URL}/seats/{seat.get('seat_id')}/status",
                            params={"status": "paid"}
                        )
                    except Exception as seat_error:
                        print(f"Error updating seat status: {seat_error}")
                
                # Tạo và gửi thông báo thanh toán thành công
                try:
                    # Lấy thông tin chi tiết về phim và ghế từ booking
                    movie_title = booking_data.get("movie_title", "")
                    # Lấy ra danh sách seat_number từ seats
                    seat_numbers = [seat.get('seat_number') for seat in booking_seats]
                    seats_str = ", ".join(seat_numbers)
                    formatted_amount = f"{payment.amount:,.0f} VND"
                    
                    # Tạo nội dung thông báo
                    notification_content = f"Thanh toán thành công! Vé xem phim '{movie_title}' (ghế {seats_str}) với số tiền {formatted_amount} đã được xác nhận."
                    
                    # Tạo thông báo
                    notification_data = {
                        "type": "payment_confirmation",
                        "customer_id": booking_data.get("customer_id"),
                        "content": notification_content,
                        "booking_id": payment.booking_id,
                        "payment_id": payment_result.get("_id", "")
                    }
                    
                    # Gửi thông báo đến notification service
                    notification_response = await client.post(
                        f"{NOTIFICATION_SERVICE_URL}/notifications",
                        json=notification_data
                    )
                    
                    print(f"Notification sent: {notification_response.status_code}")
                except Exception as notification_error:
                    # Chỉ ghi log lỗi thông báo, không ảnh hưởng đến thanh toán
                    print(f"Error sending notification: {notification_error}")
                
            return payment_result
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Payment service timeout")
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Error connecting to payment service: {str(e)}")

@app.get("/payments/{payment_id}")
async def get_payment(payment_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYMENT_SERVICE_URL}/payments/{payment_id}"
        )
        return response.json()

@app.get("/payments/booking/{booking_id}")
async def get_booking_payments(booking_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{PAYMENT_SERVICE_URL}/payments/booking/{booking_id}"
        )
        return response.json()

# Customer Routes
@app.post("/auth/login")
async def login(customer: dict):
    async with httpx.AsyncClient() as client:
        # Tiếp nhận dữ liệu email và password từ body của request, không dùng params
        response = await client.post(
            f"{CUSTOMER_SERVICE_URL}/customers/login",
            json={"email": customer.get("email"), "password": customer.get("password")}
        )
        if response.status_code != 200:
            # Nếu Customer Service trả về lỗi, chuyển tiếp lỗi đó đến client
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Lỗi xác thực")
            )
        
        # Trả về response đúng format cho frontend
        data = response.json()
        # Đảm bảo response có customer_id
        if "customer_id" not in data:
            raise HTTPException(status_code=500, detail="Invalid response from customer service")
            
        return data

@app.post("/auth/register")
async def register(customer: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CUSTOMER_SERVICE_URL}/customers", json=customer)
        if response.status_code != 200:
            # Nếu Customer Service trả về lỗi, chuyển tiếp lỗi đó đến client
            raise HTTPException(
                status_code=response.status_code,
                detail=response.json().get("detail", "Lỗi khi đăng ký")
            )
        return response.json()

@app.get("/customers/{customer_id}")
async def get_customer(customer_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}")
        return response.json()

@app.put("/customers/{customer_id}")
async def update_customer(customer_id: str, customer: dict):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{CUSTOMER_SERVICE_URL}/customers/{customer_id}",
            json=customer
        )
        return response.json()

# Notification Routes
@app.post("/notifications")
async def create_notification(notification: dict):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                json=notification
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến dịch vụ thông báo: {str(e)}")

@app.get("/notifications/{notification_id}")
async def get_notification(notification_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NOTIFICATION_SERVICE_URL}/notifications/{notification_id}"
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến dịch vụ thông báo: {str(e)}")

@app.get("/notifications/customer/{customer_id}")
async def get_customer_notifications(customer_id: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NOTIFICATION_SERVICE_URL}/notifications/customer/{customer_id}"
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến dịch vụ thông báo: {str(e)}")

@app.put("/notifications/{notification_id}/status")
async def update_notification_status(notification_id: str, status: str):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{NOTIFICATION_SERVICE_URL}/notifications/{notification_id}/status",
                params={"status": status}
            )
            return response.json()
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến dịch vụ thông báo: {str(e)}")

# New API Endpoints for Management
@app.post("/admin/showtimes/create-daily")
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
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Lấy thông tin phim từ Movie Service để xác nhận phim tồn tại
            try:
                movie_response = await client.get(f"{MOVIE_SERVICE_URL}/movies/{movie_id}")
                if movie_response.status_code != 200:
                    raise HTTPException(status_code=404, detail=f"Không tìm thấy phim với ID {movie_id}")
                
                movie_data = movie_response.json()
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến dịch vụ phim: {str(e)}")
            
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
                    response = await client.post(f"{MOVIE_SERVICE_URL}/showtimes", json=showtime_data)
                    if response.status_code == 200 or response.status_code == 201:
                        created_showtime = response.json()
                        showtimes.append(created_showtime)
                    else:
                        print(f"Lỗi khi tạo suất chiếu lúc {current_time.strftime('%H:%M')}: {response.text}")
                except httpx.RequestError as e:
                    print(f"Lỗi kết nối khi tạo suất chiếu: {str(e)}")
                
                # Cập nhật thời gian cho suất chiếu tiếp theo (thời gian kết thúc + thời gian nghỉ giữa các suất)
                current_time = showtime_end + timedelta(minutes=time_between_showtimes)
            
            return {
                "message": f"Đã tạo {len(showtimes)} suất chiếu cho ngày {date}",
                "showtimes": showtimes
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo suất chiếu: {str(e)}")

@app.post("/admin/seats/create-for-showtime/{showtime_id}")
async def create_seats_for_showtime(showtime_id: str):
    """
    Tạo tất cả các ghế từ A1 đến E10 cho một suất chiếu
    
    Lưu ý: Dữ liệu sẽ được lưu trữ trong MongoDB Atlas
    """
    try:
        async with httpx.AsyncClient() as client:
            # Kiểm tra xem showtime có tồn tại không
            try:
                showtime_response = await client.get(f"{MOVIE_SERVICE_URL}/showtimes/{showtime_id}")
                if showtime_response.status_code != 200:
                    raise HTTPException(status_code=404, detail=f"Không tìm thấy suất chiếu với ID {showtime_id}")
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến dịch vụ phim: {str(e)}")
            
            # Gọi API tạo ghế từ Seat Service
            try:
                response = await client.post(f"{SEAT_SERVICE_URL}/seats/create-for-showtime", params={"showtime_id": showtime_id})
                return response.json()
            except httpx.RequestError as e:
                raise HTTPException(status_code=500, detail=f"Lỗi kết nối đến dịch vụ ghế ngồi: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo ghế: {str(e)}") 