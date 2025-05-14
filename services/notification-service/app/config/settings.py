"""
Cấu hình ứng dụng
"""
import os
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

# MongoDB URI
MONGODB_URI = os.getenv("MONGODB_URI")

# SQS Queue URLs
BOOKING_CREATED_QUEUE_URL = os.getenv('SQS_BOOKING_CREATED_URL')
PAYMENT_PROCESSED_QUEUE_URL = os.getenv('SQS_PAYMENT_PROCESSED_URL')

# AWS credentials
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')

# CORS origins
CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000", "*"]

# Cấu hình Socket.IO
SOCKET_PING_TIMEOUT = 60
SOCKET_PING_INTERVAL = 25 