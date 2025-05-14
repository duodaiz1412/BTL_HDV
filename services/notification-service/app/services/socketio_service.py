"""
Socket.IO service functions.
"""
import socketio
import logging
from typing import Dict, Any
from app.config.settings import CORS_ORIGINS, SOCKET_PING_TIMEOUT, SOCKET_PING_INTERVAL
from app.database.mongodb import get_unread_customer_notifications

logger = logging.getLogger("notification-service")

# Mapping giữa customer_id và socket session
connected_customers = {}

# Khởi tạo Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=CORS_ORIGINS,
    logger=True,
    engineio_logger=True,
    ping_timeout=SOCKET_PING_TIMEOUT,
    ping_interval=SOCKET_PING_INTERVAL,
    always_connect=True
)

def setup_socketio(app):
    """
    Thiết lập Socket.IO với ứng dụng FastAPI
    """
    socket_app = socketio.ASGIApp(sio, app)
    app.mount("/socket.io", socket_app)
    
    # Đăng ký các event handler
    setup_event_handlers()
    
    return socket_app

def setup_event_handlers():
    """
    Thiết lập các event handler cho Socket.IO
    """
    @sio.event
    async def connect(sid, environ):
        """Xử lý khi client kết nối"""
        logger.info(f"Client kết nối Socket.IO: {sid}")
        await sio.emit('connected', {'status': 'ok', 'sid': sid}, room=sid)

    @sio.event
    async def disconnect(sid):
        """Xử lý khi client ngắt kết nối"""
        # Tìm và xóa sid khỏi connected_customers
        for customer_id, sessions in list(connected_customers.items()):
            if sid in sessions:
                connected_customers[customer_id].remove(sid)
                logger.info(f"Client {sid} disconnected from customer {customer_id}")
                # Nếu không còn session nào cho customer này, xóa customer khỏi dictionary
                if not connected_customers[customer_id]:
                    del connected_customers[customer_id]
                    logger.info(f"Removed customer {customer_id} from connected customers")
                break

    @sio.event
    async def join_room(sid, data):
        """Xử lý khi client tham gia vào phòng của khách hàng"""
        try:
            customer_id = data.get('customer_id')
            if not customer_id:
                await sio.emit('error', {'message': 'Missing customer_id'}, room=sid)
                return
            
            # Thêm sid vào danh sách session của customer
            if customer_id not in connected_customers:
                connected_customers[customer_id] = set()
            connected_customers[customer_id].add(sid)
            
            logger.info(f"Client {sid} joined room for customer {customer_id}")
            await sio.emit('joined', {'status': 'ok', 'customer_id': customer_id}, room=sid)
            
            # Gửi các thông báo chưa đọc
            unread_notifications = await get_unread_customer_notifications(customer_id)
            
            if unread_notifications:
                # Format datetime để JSON
                for notification in unread_notifications:
                    if "created_at" in notification:
                        notification["created_at"] = notification["created_at"].isoformat()
                
                await sio.emit('unread_notifications', unread_notifications, room=sid)
                logger.info(f"Sent {len(unread_notifications)} unread notifications to customer {customer_id}")
        
        except Exception as e:
            logger.error(f"Error in join_room: {e}")
            await sio.emit('error', {'message': str(e)}, room=sid)

    @sio.event
    async def mark_read(sid, data):
        """Xử lý khi client đánh dấu thông báo đã đọc"""
        try:
            from bson import ObjectId
            from app.database.mongodb import update_notification_status
            
            notification_id = data.get('notification_id')
            if not notification_id:
                await sio.emit('error', {'message': 'Missing notification_id'}, room=sid)
                return
            
            # Cập nhật trạng thái trong database
            success = await update_notification_status(notification_id, "read")
            
            if success:
                await sio.emit('notification_marked_read', {'notification_id': notification_id}, room=sid)
                logger.info(f"Notification {notification_id} marked as read")
            else:
                await sio.emit('error', {'message': 'Notification not found or already read'}, room=sid)
        
        except Exception as e:
            logger.error(f"Error in mark_read: {e}")
            await sio.emit('error', {'message': str(e)}, room=sid)

async def send_notification_to_customer(customer_id: str, notification: Dict[str, Any]):
    """Gửi thông báo tới khách hàng thông qua Socket.IO"""
    try:
        # Kiểm tra xem customer_id có trong danh sách kết nối không
        if customer_id in connected_customers:
            # Format datetime để JSON
            if "created_at" in notification and not isinstance(notification["created_at"], str):
                notification["created_at"] = notification["created_at"].isoformat()
                
            for sid in connected_customers[customer_id]:
                # Gửi thông báo tới tất cả các session của customer
                await sio.emit('notification', notification, room=sid)
                logger.info(f"Notification sent to customer {customer_id}, session {sid}")
        else:
            logger.info(f"No active connections for customer {customer_id}")
    except Exception as e:
        logger.error(f"Error sending notification via Socket.IO: {e}")

def get_active_connections():
    """Lấy thông tin về các kết nối hiện tại"""
    return {
        "active_connections": len(connected_customers),
        "customers_connected": list(connected_customers.keys())
    } 