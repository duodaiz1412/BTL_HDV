# Kiến Trúc Hệ Thống

## Tổng Quan
Hệ thống đặt vé xem phim được xây dựng theo kiến trúc microservices, cho phép khách hàng đặt vé trực tuyến một cách nhanh chóng và an toàn. Hệ thống bao gồm các thành phần chính sau:

## Các Thành Phần Hệ Thống

### Frontend Service
- **Công nghệ**: React + Tailwind CSS
- **Chức năng**: Giao diện người dùng cho việc đặt vé
- **Tính năng**: 
  - Hiển thị danh sách phim
  - Chọn suất chiếu và ghế ngồi
  - Form đặt vé và thanh toán
  - Xem lịch sử đặt vé

### API Gateway
- **Công nghệ**: Python FastAPI
- **Chức năng**: Điều hướng request đến các service
- **Tính năng**:
  - Load balancing
  - Rate limiting
  - Authentication/Authorization
  - Request/Response transformation

### Movie Service
- **Công nghệ**: Python FastAPI + MongoDB
- **Chức năng**: Quản lý thông tin phim và suất chiếu
- **Tính năng**:
  - CRUD phim
  - Quản lý suất chiếu
  - Tìm kiếm phim

### Booking Service
- **Công nghệ**: Python FastAPI + MongoDB
- **Chức năng**: Xử lý quy trình đặt vé
- **Tính năng**:
  - Tạo đơn đặt vé
  - Cập nhật trạng thái vé
  - Xử lý giao dịch (Saga Pattern)

### Seat Service
- **Công nghệ**: Python FastAPI + MongoDB
- **Chức năng**: Quản lý trạng thái ghế ngồi
- **Tính năng**:
  - Kiểm tra ghế trống
  - Khóa/giải phóng ghế
  - Cập nhật trạng thái ghế

### Payment Service
- **Công nghệ**: Python FastAPI + MongoDB
- **Chức năng**: Xử lý thanh toán
- **Tính năng**:
  - Tích hợp cổng thanh toán
  - Xử lý giao dịch
  - Hoàn tiền

### Customer Service
- **Công nghệ**: Python FastAPI + MongoDB
- **Chức năng**: Quản lý thông tin khách hàng
- **Tính năng**:
  - Đăng ký/đăng nhập
  - Quản lý profile
  - Lịch sử đặt vé

### Notification Service
- **Công nghệ**: Python FastAPI
- **Chức năng**: Gửi thông báo
- **Tính năng**:
  - Gửi email xác nhận
  - Thông báo trạng thái vé

## Giao Tiếp Giữa Các Service

### REST API
- Giao tiếp đồng bộ giữa các service
- Sử dụng FastAPI cho API endpoints
- JWT cho xác thực

### Message Queue (Kafka)
- Giao tiếp bất đồng bộ
- Xử lý các sự kiện:
  - Đặt vé thành công
  - Thanh toán hoàn tất
  - Gửi thông báo

### Saga Pattern
- Đảm bảo tính nhất quán dữ liệu
- Xử lý giao dịch phân tán
- Rollback khi có lỗi

## Luồng Dữ Liệu

1. Khách hàng chọn phim và suất chiếu
2. Kiểm tra ghế trống
3. Tạo đơn đặt vé
4. Xử lý thanh toán
5. Cập nhật trạng thái ghế
6. Gửi email xác nhận

## Khả Năng Mở Rộng & Chịu Lỗi

- Horizontal scaling cho mỗi service
- Circuit breaker pattern
- Retry mechanism
- Fallback strategies
- Monitoring và logging
- Health checks

## Bảo Mật

- JWT authentication
- HTTPS cho tất cả API
- Rate limiting
- Input validation
- Data encryption
- Role-based access control