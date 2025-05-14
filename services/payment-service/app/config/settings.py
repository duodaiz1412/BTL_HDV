import os
from dotenv import load_dotenv

# Tải các biến môi trường từ file .env nếu có
load_dotenv()

# MongoDB settings
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://admin:admin@cluster0.zqzqy.mongodb.net/")

# AWS SQS settings
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
SQS_PAYMENT_PROCESSED_URL = os.getenv("SQS_PAYMENT_PROCESSED_URL") 