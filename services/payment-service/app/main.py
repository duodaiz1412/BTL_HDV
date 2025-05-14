from fastapi import FastAPI
from app.routes import payments_router
from app.utils import setup_logger
from app.database import connect_to_db, close_db_connection
from app.services.sqs_service import SQSService

# Cấu hình logging
logger = setup_logger()

# Khởi tạo ứng dụng FastAPI
app = FastAPI(title="Payment Service")

# Đăng ký các event handler
app.add_event_handler("startup", connect_to_db)
app.add_event_handler("shutdown", close_db_connection)

# Đăng ký các router
app.include_router(payments_router)

# Endpoint kiểm tra health
@app.get("/health", tags=["health"])
async def health_check():
    """Endpoint kiểm tra trạng thái của service."""
    return {"status": "healthy"}

# Đóng SQS session khi shutdown
@app.on_event("shutdown")
def shutdown_event():
    SQSService.close_session() 