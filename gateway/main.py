import logging
import socketio
import asyncio
from starlette.responses import StreamingResponse, Response
from starlette.websockets import WebSocket
import httpx
from dotenv import load_dotenv
import os
from datetime import datetime, time, timedelta
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from motor.motor_asyncio import AsyncIOMotorClient
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request
import json

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

load_dotenv()

# Tạo FastAPI app
app = FastAPI(title="API Gateway")

# Đọc cấu hình CORS từ biến môi trường hoặc mặc định
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
try:
    if CORS_ORIGINS != "*":
        CORS_ORIGINS = json.loads(CORS_ORIGINS)  # Chuyển đổi chuỗi JSON sang list
except:
    # Nếu không thể parse JSON, sử dụng danh sách mặc định
    CORS_ORIGINS = ["*"]

# Cấu hình CORS riêng cho socketio
socketio_cors_allowed_origins = "*"  # Cho phép tất cả các nguồn gốc

# CORS middleware cho FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Cho phép tất cả các nguồn gốc
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

# Khởi tạo Socket.IO server với cấu hình CORS nâng cao
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # Cho phép tất cả các nguồn gốc
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e8,
    always_connect=True,  # Luôn cho phép kết nối
    cors_credentials=True
)

# Định nghĩa namespace
notification_namespace = '/'

# Socket.IO events
@sio.event
async def connect(sid, environ, namespace=notification_namespace):
    logger.info(f"Client connected: {sid}")
    logger.info(f"Connection details: Headers: {environ.get('headers', {})}") 
    logger.info(f"Connection details: Query: {environ.get('QUERY_STRING', '')}")
    
    client_origin = None
    for key, value in environ.get('headers', {}).items():
        if key.lower() == 'origin':
            client_origin = value
            break
    
    logger.info(f"Client origin: {client_origin}")
    
    # Lấy customer_id từ query string nếu có
    query_params = environ.get('QUERY_STRING', '')
    customer_id = None
    for param in query_params.split('&'):
        if param.startswith('customer_id='):
            customer_id = param.split('=')[1]
            break
    
    logger.info(f"Customer ID from query: {customer_id}")
    
    # Tự động đưa client vào phòng dựa trên customer_id
    if customer_id:
        room = f"customer_{customer_id}"
        await sio.enter_room(sid, room, namespace=namespace)
        logger.info(f"Đã đưa client {sid} vào phòng {room}")
    
    # Gửi thông báo chào mừng
    await sio.emit('welcome', {
        'message': 'Kết nối thành công đến API Gateway Socket.IO server',
        'sid': sid,
        'customer_id': customer_id
    }, room=sid, namespace=namespace)
    
@sio.event
async def disconnect(sid, namespace=notification_namespace):
    logger.info(f"Client disconnected: {sid}")
    # Lấy danh sách phòng của client
    rooms = sio.rooms(sid, namespace=namespace)
    logger.info(f"Client {sid} left rooms: {rooms}")

@sio.event
async def message(sid, data, namespace=notification_namespace):
    logger.info(f"Message from {sid}: {data}")
    # Gửi tin nhắn phản hồi
    await sio.emit('response', {'status': 'ok', 'message': 'Tin nhắn đã nhận'}, room=sid, namespace=namespace)
    
    # Chuyển tiếp tin nhắn đến notification service nếu cần
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/forward-message",
                json={"sid": sid, "data": data}
            )
            if response.status_code == 200:
                response_data = response.json()
                await sio.emit('notification', response_data, room=sid, namespace=namespace)
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            
@sio.event
async def join_room(sid, data, namespace=notification_namespace):
    if 'room' in data:
        room = data['room']
        await sio.enter_room(sid, room, namespace=namespace)
        logger.info(f"Client {sid} joined room: {room}")
        await sio.emit('room_joined', {'room': room}, room=sid, namespace=namespace)
        # Log danh sách phòng của client
        rooms = sio.rooms(sid, namespace=namespace)
        logger.info(f"Client {sid} rooms after join: {rooms}")

@sio.on('*', namespace=notification_namespace)
async def catch_all(event, sid, data):
    logger.info(f"Caught event: {event}, sid: {sid}, data: {data}")
    await sio.emit('echo', {'event': event, 'data': data}, room=sid, namespace=notification_namespace)

# Tạo ASGI app cho Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io',
    other_asgi_app=app
)

# Thêm route kiểm tra cho Socket.IO
@app.get("/socket-status")
async def socket_status():
    return {"status": "online", "connections": len(sio.manager.get_participants())}

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
            booking_result = response.json()
            
            # Nếu tạo booking thành công, gửi thông báo
            if response.status_code == 200:
                try:
                    # Lấy thông tin chi tiết về phim
                    movie_response = await client.get(f"{MOVIE_SERVICE_URL}/movies/{booking.movie_id}")
                    movie_data = movie_response.json()
                    movie_title = movie_data.get("title", "")
                    
                    # Lấy ra danh sách seat_number từ seats
                    seat_numbers = [seat.seat_number for seat in booking.seats]
                    seats_str = ", ".join(seat_numbers)
                    formatted_amount = f"{booking.total_amount:,.0f} VND"
                    
                    # Tạo nội dung thông báo
                    notification_content = f"Đặt vé thành công! Vé xem phim '{movie_title}' (ghế {seats_str}) với số tiền {formatted_amount}. Vui lòng thanh toán trong vòng 15 phút."
                    
                    # Tạo thông báo
                    notification_data = {
                        "type": "booking_confirmation",
                        "customer_id": booking.customer_id,
                        "content": notification_content,
                        "booking_id": booking_result.get("_id", "")
                    }
                    
                    # Gửi thông báo đến notification service và socket
                    notification_response = await client.post(
                        f"{NOTIFICATION_SERVICE_URL}/notifications",
                        json=notification_data,
                        timeout=10.0
                    )
                    
                    if notification_response.status_code == 200:
                        notification_result = notification_response.json()
                        success = await send_notification_to_customer(booking.customer_id, notification_result)
                        if success:
                            logger.info(f"Successfully sent booking notification to customer {booking.customer_id}")
                        else:
                            logger.error(f"Failed to send booking notification to customer {booking.customer_id}")
                    else:
                        logger.error(f"Failed to create notification: {notification_response.text}")
                        
                except Exception as notification_error:
                    # Chỉ ghi log lỗi thông báo, không ảnh hưởng đến booking
                    logger.error(f"Error sending notification: {notification_error}")
            
            return booking_result
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
                        json=notification_data,
                        timeout=10.0
                    )
                    
                    if notification_response.status_code != 200:
                        print(f"Lỗi từ notification service: {notification_response.text}")
                    else:
                        print(f"Notification sent: {notification_response.status_code}")
                        
                        # Gửi thông báo qua websocket
                        customer_id = booking_data.get("customer_id")
                        if customer_id:
                            try:
                                # Validate and parse notification response
                                if notification_response.status_code != 200:
                                    logger.error(f"Invalid notification response: {notification_response.text}")
                                    return  # Skip WebSocket emission if notification creation failed

                                try:
                                    notification_result = notification_response.json()
                                except json.decoder.JSONDecodeError as json_error:
                                    logger.error(f"Failed to parse notification response: {json_error}")
                                    return

                                # Send notification to customer room
                                room = f"customer_{customer_id}"
                                await sio.emit(
                                    'new_notification',
                                    notification_result,
                                    room=room,
                                    namespace=notification_namespace
                                )
                                logger.info(
                                    f"Sent payment notification via WebSocket to customer_id: {customer_id}, "
                                    f"room: {room}, message: {notification_result}"
                                )
                            except Exception as ws_error:
                                logger.error(f"Failed to send WebSocket notification for customer_id {customer_id}: {ws_error}")
                        
                except httpx.RequestError as notification_error:
                    # Chỉ ghi log lỗi thông báo, không ảnh hưởng đến thanh toán
                    print(f"Lỗi kết nối đến dịch vụ thông báo: {notification_error}")
                except httpx.TimeoutException:
                    print("Kết nối đến dịch vụ thông báo quá hạn")
                except Exception as notification_error:
                    # Chỉ ghi log lỗi thông báo, không ảnh hưởng đến thanh toán
                    print(f"Lỗi khi gửi thông báo: {notification_error}")
                
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
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/notifications",
                json=notification
            )
            
            if response.status_code == 200:
                notification_data = response.json()
                
                # Sau khi tạo thông báo thành công, gửi thông báo qua websocket
                customer_id = notification.get("customer_id")
                if customer_id:
                    success = await send_notification_to_customer(customer_id, notification_data)
                    if success:
                        logger.info(f"Successfully sent notification to customer {customer_id}")
                    else:
                        logger.error(f"Failed to send notification to customer {customer_id}")
                
                return notification_data
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lỗi từ dịch vụ thông báo: {response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến dịch vụ thông báo: {str(e)}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Kết nối đến dịch vụ thông báo quá hạn")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi tạo thông báo: {str(e)}")

@app.get("/notifications/{notification_id}")
async def get_notification(notification_id: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{NOTIFICATION_SERVICE_URL}/notifications/{notification_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lỗi từ dịch vụ thông báo: {response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến dịch vụ thông báo: {str(e)}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Kết nối đến dịch vụ thông báo quá hạn")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thông báo: {str(e)}")

@app.get("/notifications/customer/{customer_id}")
async def get_customer_notifications(customer_id: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{NOTIFICATION_SERVICE_URL}/notifications/customer/{customer_id}"
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lỗi từ dịch vụ thông báo: {response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến dịch vụ thông báo: {str(e)}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Kết nối đến dịch vụ thông báo quá hạn")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi lấy thông báo: {str(e)}")

@app.put("/notifications/{notification_id}/status")
async def update_notification_status(notification_id: str, status: str):
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.put(
                f"{NOTIFICATION_SERVICE_URL}/notifications/{notification_id}/status",
                params={"status": status}
            )
            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Lỗi từ dịch vụ thông báo: {response.text}"
                )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Không thể kết nối đến dịch vụ thông báo: {str(e)}")
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Kết nối đến dịch vụ thông báo quá hạn")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi khi cập nhật trạng thái thông báo: {str(e)}")

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

# Hàm tiện ích để gửi thông báo qua socket
async def send_notification_to_customer(customer_id: str, notification_data: dict):
    try:
        room = f"customer_{customer_id}"
        # Kiểm tra xem phòng có tồn tại không
        room_size = len(await sio.manager.get_room_members(room, namespace=notification_namespace))
        logger.info(f"Room {room} has {room_size} members")
        
        # Gửi thông báo
        await sio.emit(
            'new_notification',
            notification_data,
            room=room,
            namespace=notification_namespace
        )
        logger.info(f"Sent notification to room {room}: {notification_data}")
        
        return True
    except Exception as e:
        logger.error(f"Error sending notification via socket: {str(e)}")
        return False

# Export ứng dụng ASGI
app = socket_app 