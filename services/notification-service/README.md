# Notification Service

Dịch vụ thông báo (Notification Service) là một microservice trong hệ thống đặt vé xem phim, chịu trách nhiệm xử lý và gửi thông báo đến người dùng.

## Các tính năng

- Thu nhận thông báo từ SQS queues (booking confirmations, payment confirmations)
- Lưu trữ thông báo trong MongoDB
- API để tạo và quản lý thông báo

## Công nghệ sử dụng

- FastAPI - framework web
- MongoDB - cơ sở dữ liệu lưu trữ thông báo
- AWS SQS - nhận thông báo từ các dịch vụ khác

## API Endpoints

### Notifications API

- `POST /notifications` - Tạo thông báo mới
- `GET /notifications/{notification_id}` - Lấy thông tin thông báo
- `GET /notifications/customer/{customer_id}` - Lấy danh sách thông báo của khách hàng
- `PUT /notifications/{notification_id}/status` - Cập nhật trạng thái thông báo

## Lưu trữ dữ liệu

Thông báo được lưu trong MongoDB với cấu trúc sau:

```json
{
  "_id": "ObjectId",
  "type": "booking_confirmation",
  "customer_id": "customer123",
  "booking_id": "booking123",
  "payment_id": "payment123",
  "content": "Thông báo xác nhận đặt vé",
  "status": "pending",
  "created_at": "2023-01-01T00:00:00Z"
}
```

Trạng thái thông báo có thể là:
- `pending` - chưa được gửi
- `sent` - đã gửi
- `read` - đã đọc

## Cài đặt

1. Clone repository
2. Tạo và cấu hình file `.env` với các thông tin:
   ```
   MONGODB_URI=mongodb://username:password@mongodb:27017/notification_db
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=ap-southeast-1
   SQS_BOOKING_CREATED_URL=https://sqs.ap-southeast-1.amazonaws.com/123456789012/booking-created
   SQS_PAYMENT_PROCESSED_URL=https://sqs.ap-southeast-1.amazonaws.com/123456789012/payment-processed
   ```
3. Chạy service:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8006 --reload
   ```

## Sử dụng Docker

```bash
docker build -t notification-service .
docker run -p 8006:8006 --env-file .env notification-service
```

## Làm thế nào để sử dụng Notification API

Để lấy thông báo của một khách hàng, frontend cần gọi API `GET /notifications/customer/{customer_id}` định kỳ.

### Ví dụ sử dụng API để lấy thông báo:

```javascript
async function fetchNotifications(customerId) {
  try {
    const response = await fetch(`http://localhost:8006/notifications/customer/${customerId}`);
    if (!response.ok) {
      throw new Error('Lỗi khi lấy thông báo');
    }
    const notifications = await response.json();
    return notifications;
  } catch (error) {
    console.error('Không thể lấy thông báo:', error);
    return [];
  }
}

// Gọi hàm này định kỳ để cập nhật thông báo
setInterval(() => {
  fetchNotifications('customer123').then(notifications => {
    // Xử lý và hiển thị thông báo
    console.log('Danh sách thông báo:', notifications);
  });
}, 10000); // Cập nhật mỗi 10 giây
```

### Tạo một thông báo mới

```javascript
async function createNotification(data) {
  try {
    const response = await fetch('http://localhost:8006/notifications', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    
    if (!response.ok) {
      throw new Error('Lỗi khi tạo thông báo');
    }
    
    return await response.json();
  } catch (error) {
    console.error('Không thể tạo thông báo:', error);
    return null;
  }
}

// Ví dụ sử dụng
createNotification({
  type: 'custom',
  customer_id: 'customer123',
  content: 'Đây là một thông báo tùy chỉnh!'
}); 