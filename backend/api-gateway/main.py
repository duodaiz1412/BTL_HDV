from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
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
MOVIE_SERVICE_URL = os.getenv("MOVIE_SERVICE_URL", "http://localhost:8001")
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://localhost:8002")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://localhost:8003")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8004")
SEAT_SERVICE_URL = os.getenv("SEAT_SERVICE_URL", "http://localhost:8005")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:8006")

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
async def get_movie_showtimes_v2(movie_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MOVIE_SERVICE_URL}/showtimes/movie/{movie_id}")
        return response.json()

@app.get("/showtimes/movie/{movie_id}")
async def get_movie_showtimes(movie_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MOVIE_SERVICE_URL}/showtimes/movie/{movie_id}")
        return response.json()

# Seat Routes
@app.get("/seats/showtime/{showtime_id}")
async def get_showtime_seats(showtime_id: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{SEAT_SERVICE_URL}/seats/showtime/{showtime_id}")
        return response.json()

@app.post("/seats/check")
async def check_seats(showtime_id: str, seats: List[str]):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{SEAT_SERVICE_URL}/seats/check",
            json={"showtime_id": showtime_id, "seats": seats}
        )
        return response.json()

# Booking Routes
@app.post("/bookings")
async def create_booking(booking: dict):
    async with httpx.AsyncClient() as client:
        # Check seats availability
        response = await client.post(
            f"{SEAT_SERVICE_URL}/seats/check",
            json={"showtime_id": booking["showtime_id"], "seats": booking["seats"]}
        )
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Seats are not available")
        
        # Create booking
        response = await client.post(
            f"{BOOKING_SERVICE_URL}/bookings",
            json=booking
        )
        return response.json()

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
async def create_payment(payment: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{PAYMENT_SERVICE_URL}/payments",
            json=payment
        )
        return response.json()

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
@app.post("/customers")
async def create_customer(customer: dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{CUSTOMER_SERVICE_URL}/customers", json=customer)
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