from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
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
class BookingRequest(BaseModel):
    customer_id: str
    movie_id: str
    showtime_id: str
    seats: List[str]
    total_amount: float
    status: str = "pending"

class PaymentRequest(BaseModel):
    booking_id: str
    amount: float
    payment_method: str
    status: str = "pending"

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
            # Check seats availability
            response = await client.post(
                f"{SEAT_SERVICE_URL}/seats/check",
                params={"showtime_id": booking.showtime_id},
                json=booking.seats
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Seats are not available")
            
            # Create booking
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

            # Tạo payment
            response = await client.post(
                f"{PAYMENT_SERVICE_URL}/payments",
                json=payment.dict()
            )
            if response.status_code == 200:
                # Cập nhật trạng thái booking
                await client.put(
                    f"{BOOKING_SERVICE_URL}/bookings/{payment.booking_id}/status",
                    params={"status": "paid"}
                )
            return response.json()
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
        response = await client.post(
            f"{CUSTOMER_SERVICE_URL}/customers/login",
            params={"email": customer.get("email"), "password": customer.get("password")}
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