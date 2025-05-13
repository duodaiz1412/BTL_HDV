import { io } from 'socket.io-client';

const SOCKET_URL = 'http://localhost:8000';

class SocketService {
  constructor() {
    this.socket = null;
    this.customerId = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect(customerId) {
    if (this.socket && this.socket.connected) {
      console.log('Socket already connected');
      return this.socket;
    }

    this.customerId = customerId;
    
    // Khởi tạo kết nối socket với query parameter customer_id
    this.socket = io(SOCKET_URL, {
      query: { customer_id: customerId },
      transports: ['websocket', 'polling'], // Thêm polling làm fallback
      path: '/socket.io',
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      timeout: 20000,
      autoConnect: true
    });

    // Xử lý sự kiện kết nối
    this.socket.on('connect', () => {
      console.log('Socket connected with ID:', this.socket.id);
      this.reconnectAttempts = 0;
      
      // Gửi lại customer_id sau khi kết nối lại
      this.socket.emit('join_room', { room: `customer_${this.customerId}` });
    });

    // Xử lý sự kiện ngắt kết nối
    this.socket.on('disconnect', (reason) => {
      console.log('Socket disconnected:', reason);
      
      // Thử kết nối lại nếu chưa vượt quá số lần thử
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
        setTimeout(() => {
          if (!this.socket.connected) {
            this.socket.connect();
          }
        }, 1000);
      }
    });

    // Xử lý sự kiện lỗi
    this.socket.on('error', (error) => {
      console.error('Socket error:', error);
    });

    // Xử lý sự kiện connect_error
    this.socket.on('connect_error', (error) => {
      console.error('Connection error:', error);
    });

    // Xử lý sự kiện welcome
    this.socket.on('welcome', (data) => {
      console.log('Welcome message:', data);
    });

    // Xử lý sự kiện room_joined
    this.socket.on('room_joined', (data) => {
      console.log('Joined room:', data);
    });

    // Xử lý sự kiện reconnect
    this.socket.on('reconnect', (attemptNumber) => {
      console.log('Socket reconnected after', attemptNumber, 'attempts');
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.customerId = null;
      this.reconnectAttempts = 0;
    }
  }

  // Đăng ký callback cho sự kiện new_notification
  onNewNotification(callback) {
    if (!this.socket) {
      console.error('Socket not connected');
      return;
    }
    // Xóa listener cũ nếu có
    this.socket.off('new_notification');
    // Thêm listener mới
    this.socket.on('new_notification', (data) => {
      console.log('Received notification:', data);
      callback(data);
    });
  }

  // Hủy đăng ký callback cho sự kiện new_notification
  offNewNotification(callback) {
    if (!this.socket) {
      console.error('Socket not connected');
      return;
    }
    this.socket.off('new_notification', callback);
  }

  // Kiểm tra trạng thái kết nối
  isConnected() {
    return this.socket && this.socket.connected;
  }

  // Kết nối lại thủ công
  reconnect() {
    if (this.socket && !this.socket.connected && this.customerId) {
      this.socket.connect();
    }
  }
}

// Export singleton instance
export default new SocketService(); 