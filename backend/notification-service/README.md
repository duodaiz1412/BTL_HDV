# Notification Service

Dịch vụ quản lý và gửi thông báo cho người dùng trong hệ thống đặt vé xem phim.

## Tính năng

- Nhận thông báo từ các dịch vụ khác thông qua AWS SQS
- Lưu trữ thông báo trong MongoDB
- Gửi thông báo real-time đến người dùng qua WebSocket (Socket.IO)
- API RESTful để tạo và quản lý thông báo

## Yêu cầu

- Python 3.8+
- MongoDB
- AWS SQS (tùy chọn)

## Cài đặt

1. Cài đặt các thư viện phụ thuộc:

```bash
pip install -r requirements.txt
```

2. Tạo file .env với nội dung:

```
MONGODB_URI=mongodb://localhost:27017
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=your_aws_region
SQS_BOOKING_CREATED_URL=https://sqs.region.amazonaws.com/account/booking-created-queue
SQS_PAYMENT_PROCESSED_URL=https://sqs.region.amazonaws.com/account/payment-processed-queue
```

## Chạy dịch vụ

Chạy dịch vụ với lệnh:

```bash
uvicorn main:socket_app --host 0.0.0.0 --port 8005 --reload
```

## API Endpoints

### Tạo thông báo mới

```
POST /notifications
```

Body:
```json
{
  "type": "string",
  "customer_id": "string",
  "content": "string",
  "status": "pending",
  "booking_id": "string", // tùy chọn
  "payment_id": "string"  // tùy chọn
}
```

### Lấy thông báo theo ID

```
GET /notifications/{notification_id}
```

### Lấy tất cả thông báo của một khách hàng

```
GET /notifications/customer/{customer_id}
```

### Cập nhật trạng thái thông báo

```
PUT /notifications/{notification_id}/status?status=read
```

## Socket.IO Events

### Client-to-Server

- `join_room`: Client tham gia vào phòng của khách hàng
  ```javascript
  socket.emit('join_room', { customer_id: 'customer_id' });
  ```

### Server-to-Client

- `notification`: Server gửi thông báo đến client
  ```javascript
  socket.on('notification', function(data) {
    console.log('Nhận thông báo:', data);
  });
  ```

## Kiểm tra

Sử dụng script `trigger_notification.py` để kiểm tra việc gửi thông báo:

```bash
python trigger_notification.py <customer_id> "Nội dung thông báo kiểm tra"
```

Hoặc truy cập trang `test_socket.html` trên trình duyệt để kiểm tra kết nối Socket.IO. 