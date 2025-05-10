# 📊 Hệ Thống Đặt Vé Xem Phim - Phân Tích và Thiết Kế

## 1. 🎯 Mô Tả Nghiệp Vụ

Hệ thống đặt vé xem phim cho phép khách hàng:
- Chọn phim, suất chiếu và ghế ngồi
- Đặt vé trực tuyến
- Thanh toán và nhận xác nhận qua email

### Người Dùng
- Khách hàng đặt vé
- Quản trị viên hệ thống

### Mục Tiêu Chính
- Đơn giản hóa quy trình đặt vé
- Quản lý thông tin phim và suất chiếu
- Xử lý thanh toán an toàn
- Gửi thông báo xác nhận tự động

### Dữ Liệu Xử Lý
- Thông tin phim và suất chiếu
- Thông tin khách hàng
- Thông tin đặt vé và thanh toán
- Trạng thái ghế ngồi

## 2. 🧩 Các Microservices

| Service Name | Trách Nhiệm | Tech Stack |
|--------------|-------------|------------|
| movie-service | Quản lý thông tin phim, suất chiếu | Python FastAPI |
| booking-service | Xử lý quy trình đặt vé | Python FastAPI |
| customer-service | Quản lý thông tin khách hàng | Python FastAPI |
| payment-service | Xử lý thanh toán | Python FastAPI |
| seat-service | Quản lý trạng thái ghế ngồi | Python FastAPI |
| notification-service | Gửi email xác nhận | Python FastAPI |
| api-gateway | Điều hướng request | Python FastAPI |

## 3. 🔄 Giao Tiếp Giữa Các Service

- Sử dụng Kafka cho giao tiếp bất đồng bộ
- REST API cho giao tiếp đồng bộ
- Pattern Saga để đảm bảo tính nhất quán dữ liệu

### Luồng Giao Tiếp
1. API Gateway -> Movie Service: Lấy thông tin phim
2. API Gateway -> Seat Service: Kiểm tra ghế trống
3. Booking Service -> Payment Service: Xử lý thanh toán
4. Booking Service -> Notification Service: Gửi email xác nhận

## 4. 🗂️ Thiết Kế Dữ Liệu

### MongoDB Collections

#### Movie Service
```json
{
  "movies": {
    "_id": "ObjectId",
    "title": "String",
    "description": "String",
    "duration": "Number",
    "showtimes": [{
      "id": "String",
      "time": "DateTime",
      "theater": "String"
    }]
  }
}
```

#### Seat Service
```json
{
  "seats": {
    "_id": "ObjectId",
    "showtime_id": "String",
    "seat_number": "String",
    "status": "String",
    "booking_id": "String"
  }
}
```

#### Booking Service
```json
{
  "bookings": {
    "_id": "ObjectId",
    "customer_id": "String",
    "movie_id": "String",
    "showtime_id": "String",
    "seats": ["String"],
    "total_amount": "Number",
    "status": "String",
    "payment_id": "String"
  }
}
```

## 5. 🔐 Bảo Mật

- JWT cho xác thực
- Mã hóa dữ liệu nhạy cảm
- Rate limiting cho API
- Validation đầu vào

## 6. 📦 Kế Hoạch Triển Khai

- Docker cho containerization
- Docker Compose cho môi trường development
- MongoDB cho database
- Kafka cho message queue

## 7. 🎨 Sơ Đồ Kiến Trúc

```
+-------------+     +----------------+     +----------------+
|   Frontend  | --> |  API Gateway   | --> | Movie Service  |
|  (React)    |     |                |     |                |
+-------------+     +----------------+     +----------------+
                           |
                           v
+----------------+     +----------------+     +----------------+
| Booking Service| <-> | Payment Service| <-> | Customer Service|
+----------------+     +----------------+     +----------------+
                           |
                           v
+----------------+     +----------------+
| Seat Service   | <-> | Notification   |
|                |     | Service        |
+----------------+     +----------------+
```

## ✅ Tóm Tắt

Kiến trúc microservices được chọn vì:
- Khả năng mở rộng cao
- Dễ dàng bảo trì và phát triển
- Tách biệt các chức năng nghiệp vụ
- Xử lý đồng thời nhiều request
- Dễ dàng thêm tính năng mới

## Tác Giả

- Email: hungdn@ptit.edu.vn
- GitHub: hungdn1701

Good luck! 💪🚀
