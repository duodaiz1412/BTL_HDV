import os
import json
from dotenv import load_dotenv

load_dotenv()

# CORS settings
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
try:
    if CORS_ORIGINS != "*":
        CORS_ORIGINS = json.loads(CORS_ORIGINS)  # Chuyển đổi chuỗi JSON sang list
except:
    # Nếu không thể parse JSON, sử dụng danh sách mặc định
    CORS_ORIGINS = ["*"]

# Service URLs
MOVIE_SERVICE_URL = os.getenv("MOVIE_SERVICE_URL", "http://movie-service:8000")
BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://booking-service:8000")
CUSTOMER_SERVICE_URL = os.getenv("CUSTOMER_SERVICE_URL", "http://customer-service:8000")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8000")
SEAT_SERVICE_URL = os.getenv("SEAT_SERVICE_URL", "http://seat-service:8000")
NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8000")

# Socket.IO settings
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"  # Cho phép tất cả các nguồn gốc 