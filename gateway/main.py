from fastapi import FastAPI
import socketio
from app.utils.logger import logger
from app.sockets.socket_manager import sio
from app.middleware.cors_middleware import setup_cors
from app.routes import (
    movie_routes, 
    seat_routes, 
    booking_routes, 
    payment_routes, 
    customer_routes, 
    notification_routes, 
    admin_routes
)

# Tạo FastAPI app
app = FastAPI(title="API Gateway")

# Thiết lập CORS middleware
setup_cors(app)

# Đăng ký các router
app.include_router(movie_routes.router)
app.include_router(seat_routes.router)
app.include_router(booking_routes.router)
app.include_router(payment_routes.router)
app.include_router(customer_routes.router)
app.include_router(notification_routes.router)
app.include_router(admin_routes.router)

# Tạo ASGI app cho Socket.IO
socket_app = socketio.ASGIApp(
    sio,
    socketio_path='/socket.io',
    other_asgi_app=app
)

# Thêm route kiểm tra cho Socket.IO
@app.get("/socket-status")
async def socket_status():
    """Kiểm tra trạng thái kết nối Socket.IO"""
    return {"status": "online", "connections": len(sio.manager.get_participants())}

# Thay đổi app gốc thành socket_app
app = socket_app 