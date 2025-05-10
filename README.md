# 🎬 Hệ Thống Đặt Vé Xem Phim

Hệ thống đặt vé xem phim trực tuyến được xây dựng theo kiến trúc microservices, cho phép khách hàng đặt vé một cách nhanh chóng và an toàn.

## 🚀 Tính Năng Chính

- Xem danh sách phim và suất chiếu
- Chọn ghế ngồi trực tuyến
- Đặt vé và thanh toán
- Nhận xác nhận qua email
- Quản lý thông tin cá nhân
- Xem lịch sử đặt vé

## 🛠 Công Nghệ Sử Dụng

### Backend
- Python FastAPI
- MongoDB
- Kafka
- Docker
- JWT Authentication

### Frontend
- React
- Tailwind CSS
- Axios
- React Router

## 📦 Cài Đặt

### Yêu Cầu Hệ Thống
- Docker và Docker Compose
- Node.js 16+
- Python 3.8+

### Backend
```bash
cd backend
# Cài đặt dependencies cho từng service
cd movie-service && pip install -r requirements.txt
cd ../booking-service && pip install -r requirements.txt
# ... tương tự cho các service khác

# Chạy các service bằng Docker Compose
docker-compose up
```

### Frontend
```bash
cd frontend
npm install
npm start
```

## 🏗 Kiến Trúc Hệ Thống

Hệ thống được chia thành các microservices:

1. **Movie Service**: Quản lý thông tin phim và suất chiếu
2. **Booking Service**: Xử lý quy trình đặt vé
3. **Customer Service**: Quản lý thông tin khách hàng
4. **Payment Service**: Xử lý thanh toán
5. **Seat Service**: Quản lý trạng thái ghế ngồi
6. **Notification Service**: Gửi thông báo
7. **API Gateway**: Điều hướng request

## 🔄 Quy Trình Đặt Vé

1. Khách hàng chọn phim và suất chiếu
2. Hệ thống kiểm tra ghế trống
3. Khách hàng chọn ghế và nhập thông tin
4. Hệ thống xử lý thanh toán
5. Gửi email xác nhận
6. Cập nhật trạng thái ghế

## 🔐 Bảo Mật

- JWT Authentication
- HTTPS
- Rate Limiting
- Input Validation
- Data Encryption

## 📝 API Documentation

API documentation có sẵn tại `/docs` endpoint của mỗi service khi chạy ở môi trường development.

## 🤝 Đóng Góp

1. Fork dự án
2. Tạo branch mới (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên branch (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## 📄 License

MIT License - xem file [LICENSE](LICENSE) để biết thêm chi tiết.

## 👥 Tác Giả

- Email: hungdn@ptit.edu.vn
- GitHub: hungdn1701

