from fastapi import FastAPI
from app.routes import seats_router
from app.utils import setup_logger
from app.database import client
from app.config.settings import load_dotenv

# Load environment variables
load_dotenv()

# Cấu hình logging
logger = setup_logger()

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Seat Service")

# Đăng ký các router
app.include_router(seats_router)

@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint kiểm tra trạng thái của service."""
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    client.close() 