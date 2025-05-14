"""
Main application file.
"""
from fastapi import FastAPI
from app.routes import movies_router
from app.utils import setup_logger

# Cấu hình logging
logger = setup_logger()

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Movie Service")

# Đăng ký router
app.include_router(movies_router)

@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint kiểm tra trạng thái của service."""
    return {"status": "healthy"} 