"""
Main application file.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routes import notifications_router, admin_router
from app.utils import setup_logger
from app.services import setup_socketio, startup, shutdown
from app.config.settings import CORS_ORIGINS

# Cấu hình logging
logger = setup_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Khởi tạo các kết nối khi ứng dụng bắt đầu
    await startup()
    yield
    # Đóng các kết nối khi ứng dụng kết thúc
    await shutdown()

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Notification Service", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Thiết lập Socket.IO
setup_socketio(app)

# Đăng ký routers
app.include_router(notifications_router)
app.include_router(admin_router)

@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint kiểm tra trạng thái của service."""
    return {"status": "healthy"} 