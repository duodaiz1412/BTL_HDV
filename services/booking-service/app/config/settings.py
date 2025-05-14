import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")

# SQS Queue URLs
BOOKING_CREATED_QUEUE_URL = os.getenv("SQS_BOOKING_CREATED_URL")
PAYMENT_PROCESSED_QUEUE_URL = os.getenv("SQS_PAYMENT_PROCESSED_URL")
SEATS_BOOKED_QUEUE_URL = os.getenv("SQS_SEATS_BOOKED_URL")

# AWS Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# Service URLs
SEAT_SERVICE_URL = os.getenv("SEAT_SERVICE_URL", "http://seat-service:8000") 