import socketio
from app.utils.logger import logger
from app.config.settings import SOCKETIO_CORS_ALLOWED_ORIGINS, NOTIFICATION_SERVICE_URL
import httpx

# Khởi tạo Socket.IO server với cấu hình CORS nâng cao
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins="*",  # Cho phép tất cả các nguồn gốc
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25,
    max_http_buffer_size=1e8,
    always_connect=True,  # Luôn cho phép kết nối
    cors_credentials=True
)

# Định nghĩa namespace
notification_namespace = '/'

# Socket.IO events
@sio.event
async def connect(sid, environ, namespace=notification_namespace):
    logger.info(f"Client connected: {sid}")
    logger.info(f"Connection details: Headers: {environ.get('headers', {})}") 
    logger.info(f"Connection details: Query: {environ.get('QUERY_STRING', '')}")
    
    client_origin = None
    for key, value in environ.get('headers', {}).items():
        if key.lower() == 'origin':
            client_origin = value
            break
    
    logger.info(f"Client origin: {client_origin}")
    
    # Lấy customer_id từ query string nếu có
    query_params = environ.get('QUERY_STRING', '')
    customer_id = None
    for param in query_params.split('&'):
        if param.startswith('customer_id='):
            customer_id = param.split('=')[1]
            break
    
    logger.info(f"Customer ID from query: {customer_id}")
    
    # Tự động đưa client vào phòng dựa trên customer_id
    if customer_id:
        room = f"customer_{customer_id}"
        await sio.enter_room(sid, room, namespace=namespace)
        logger.info(f"Đã đưa client {sid} vào phòng {room}")
    
    # Gửi thông báo chào mừng
    await sio.emit('welcome', {
        'message': 'Kết nối thành công đến API Gateway Socket.IO server',
        'sid': sid,
        'customer_id': customer_id
    }, room=sid, namespace=namespace)
    
@sio.event
async def disconnect(sid, namespace=notification_namespace):
    logger.info(f"Client disconnected: {sid}")
    # Lấy danh sách phòng của client
    rooms = sio.rooms(sid, namespace=namespace)
    logger.info(f"Client {sid} left rooms: {rooms}")

@sio.event
async def message(sid, data, namespace=notification_namespace):
    logger.info(f"Message from {sid}: {data}")
    # Gửi tin nhắn phản hồi
    await sio.emit('response', {'status': 'ok', 'message': 'Tin nhắn đã nhận'}, room=sid, namespace=namespace)
    
    # Chuyển tiếp tin nhắn đến notification service nếu cần
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{NOTIFICATION_SERVICE_URL}/forward-message",
                json={"sid": sid, "data": data}
            )
            if response.status_code == 200:
                response_data = response.json()
                await sio.emit('notification', response_data, room=sid, namespace=namespace)
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            
@sio.event
async def join_room(sid, data, namespace=notification_namespace):
    if 'room' in data:
        room = data['room']
        await sio.enter_room(sid, room, namespace=namespace)
        logger.info(f"Client {sid} joined room: {room}")
        await sio.emit('room_joined', {'room': room}, room=sid, namespace=namespace)
        # Log danh sách phòng của client
        rooms = sio.rooms(sid, namespace=namespace)
        logger.info(f"Client {sid} rooms after join: {rooms}")

@sio.on('*', namespace=notification_namespace)
async def catch_all(event, sid, data):
    logger.info(f"Caught event: {event}, sid: {sid}, data: {data}")
    await sio.emit('echo', {'event': event, 'data': data}, room=sid, namespace=notification_namespace)

# Hàm tiện ích để gửi thông báo qua socket
async def send_notification_to_customer(customer_id: str, notification_data: dict):
    try:
        room = f"customer_{customer_id}"
        
        # Gửi thông báo mà không cần kiểm tra số lượng thành viên trong phòng
        await sio.emit(
            'new_notification',
            notification_data,
            room=room,
            namespace=notification_namespace
        )
        logger.info(f"Sent notification to room {room}: {notification_data}")
        
        return True
    except Exception as e:
        logger.error(f"Error sending notification to customer {customer_id}: {e}")
        return False 