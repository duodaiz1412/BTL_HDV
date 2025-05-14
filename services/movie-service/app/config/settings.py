"""
Cấu hình ứng dụng
"""
import os
from dotenv import load_dotenv

# Load biến môi trường
load_dotenv()

# MongoDB URI
MONGODB_URI = os.getenv("MONGODB_URI") 