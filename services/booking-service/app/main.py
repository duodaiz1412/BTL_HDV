from fastapi import FastAPI
from app.routes import bookings_router, resources_router
from app.utils import setup_logger
from app.services.sqs_service import close_sqs_session

# Cấu hình logging
logger = setup_logger()

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Booking Service")

# Đăng ký các router
app.include_router(bookings_router)
app.include_router(resources_router)

@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint kiểm tra trạng thái của service."""
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """Xử lý khi ứng dụng shutdown."""
    close_sqs_session() 