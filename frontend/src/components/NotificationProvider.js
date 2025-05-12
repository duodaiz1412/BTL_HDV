import React, { createContext, useState, useEffect, useContext } from 'react';
import { io } from 'socket.io-client';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { getNotifications } from '../services/api';

const NotificationContext = createContext();

export const useNotifications = () => useContext(NotificationContext);

export const NotificationProvider = ({ children }) => {
  const [socket, setSocket] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [socketStatus, setSocketStatus] = useState('disconnected');

  // Lấy thông báo ban đầu từ API
  useEffect(() => {
    const customerId = localStorage.getItem('customer_id');
    if (customerId) {
      const fetchNotifications = async () => {
        try {
          const response = await getNotifications();
          console.log('Dữ liệu thông báo đã tải:', response.data);
          setNotifications(response.data || []);
        } catch (error) {
          console.error('Lỗi khi lấy thông báo:', error);
        } finally {
          setLoading(false);
        }
      };
      fetchNotifications();
    } else {
      setLoading(false);
    }
  }, []);

  // Kết nối websocket để nhận thông báo realtime
  useEffect(() => {
    console.log('Bắt đầu kết nối WebSocket...');
    
    // Kết nối đến Socket.IO server với các tùy chọn cấu hình đúng
    const socketOptions = {
      transports: ['websocket', 'polling'], // Thử kết nối WebSocket trước, rồi quay lại polling nếu cần
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      autoConnect: true,
      forceNew: true,
      timeout: 10000
    };
    
    console.log('Cấu hình Socket.IO:', socketOptions);
    const socketInstance = io('http://localhost:8007', socketOptions);
    
    setSocket(socketInstance);
    
    // Xử lý kết nối
    socketInstance.on('connect', () => {
      console.log('Kết nối đến notification service thành công!', socketInstance.id);
      setSocketStatus('connected');
      
      // Lấy customer_id từ localStorage nếu có
      const customerId = localStorage.getItem('customer_id');
      if (customerId) {
        // Tham gia vào phòng của khách hàng
        console.log('Tham gia vào phòng cho customer_id:', customerId);
        socketInstance.emit('join_room', { customer_id: customerId });
      }
    });

    // Xử lý nhận thông báo
    socketInstance.on('notification', (data) => {
      console.log('Nhận thông báo mới:', data);
      const customerId = localStorage.getItem('customer_id');
      
      // Chỉ hiển thị thông báo cho đúng khách hàng
      if (customerId && data.customer_id === customerId) {
        // Hiển thị toast thông báo
        toast.success(data.content, {
          position: "top-right",
          autoClose: 5000,
          hideProgressBar: false,
          closeOnClick: true,
          pauseOnHover: true,
          draggable: true,
        });
        
        // Cập nhật danh sách thông báo
        setNotifications(prev => [data, ...prev]);
      }
    });

    // Xử lý lỗi
    socketInstance.on('connect_error', (err) => {
      console.error('Lỗi kết nối đến notification service:', err);
      setSocketStatus('error: ' + err.message);
    });

    socketInstance.on('error', (err) => {
      console.error('Lỗi Socket.IO:', err);
      setSocketStatus('socket error');
    });

    socketInstance.on('reconnect_attempt', (attempt) => {
      console.log(`Đang thử kết nối lại lần ${attempt}...`);
      setSocketStatus(`reconnecting (${attempt})`);
    });

    socketInstance.on('reconnect_failed', () => {
      console.error('Không thể kết nối lại sau nhiều lần thử');
      setSocketStatus('reconnect failed');
    });
    
    socketInstance.on('disconnect', (reason) => {
      console.log('Socket bị ngắt kết nối:', reason);
      setSocketStatus('disconnected: ' + reason);
    });

    // Dọn dẹp khi component unmount
    return () => {
      console.log('Ngắt kết nối WebSocket...');
      socketInstance.disconnect();
    };
  }, []);

  // Debug: Hiển thị thông báo trong console mỗi khi socketStatus thay đổi
  useEffect(() => {
    console.log('Trạng thái Socket:', socketStatus);
  }, [socketStatus]);

  // Đảm bảo context luôn có giá trị mới nhất
  const contextValue = {
    notifications,
    loading,
    socketStatus,
    markAsRead: (notificationId) => {
      // Cập nhật trạng thái đã đọc cho thông báo
      setNotifications(notifications.map(n => 
        n._id === notificationId ? { ...n, status: 'read' } : n
      ));
    }
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      <ToastContainer />
    </NotificationContext.Provider>
  );
};

export default NotificationProvider; 