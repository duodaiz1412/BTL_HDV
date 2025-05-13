import React, { createContext, useState, useEffect, useContext } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { getNotifications, markNotificationAsRead } from '../services/api';
import { io } from 'socket.io-client';

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

  // Kết nối Socket.IO để nhận thông báo realtime
  useEffect(() => {
    console.log('=== Bắt đầu kết nối Socket.IO... ===');
    
    const customerId = localStorage.getItem('customer_id');
    if (!customerId) {
      console.log('Không tìm thấy customer_id, không thể kết nối Socket.IO');
      setSocketStatus('no customer_id');
      return;
    }
    
    // Kết nối đến Socket.IO server qua API Gateway
    const socketUrl = 'http://localhost:8000';
    console.log('Kết nối Socket.IO đến API Gateway:', socketUrl);
    
    // Cập nhật cấu hình Socket.IO để phù hợp với API Gateway mới
    const newSocket = io(socketUrl, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],  // Ưu tiên websocket trước
      reconnectionAttempts: 10,
      reconnectionDelay: 1000,
      timeout: 20000,
      query: { customer_id: customerId },  // Truyền customer_id qua query params
    });
    
    setSocket(newSocket);
    
    // Xử lý các sự kiện Socket.IO
    newSocket.on('connect', () => {
      console.log('=== Socket.IO: Kết nối đã mở ===');
      console.log('Socket ID:', newSocket.id);
      setSocketStatus('connected');
      
      // Tham gia room của khách hàng sau khi kết nối thành công
      newSocket.emit('join_room', { room: `customer_${customerId}` });
      console.log('Đã gửi yêu cầu tham gia room:', `customer_${customerId}`);
    });

    // Xử lý sự kiện chào mừng (đã thêm trong API Gateway)
    newSocket.on('welcome', (data) => {
      console.log('=== Socket.IO: Thông điệp chào mừng ===');
      console.log('Chi tiết:', JSON.stringify(data, null, 2));
      setSocketStatus('connected');
    });
    
    newSocket.on('disconnect', (reason) => {
      console.log('=== Socket.IO: Đã ngắt kết nối ===');
      console.log('Lý do:', reason);
      setSocketStatus('disconnected');
    });
    
    newSocket.on('connect_error', (error) => {
      console.error('=== Socket.IO: Lỗi kết nối ===');
      console.error('Chi tiết lỗi:', error);
      setSocketStatus('error');
    });
    
    newSocket.on('room_joined', (data) => {
      console.log('=== Socket.IO: Đã tham gia room ===');
      console.log('Chi tiết:', JSON.stringify(data, null, 2));
    });
    
    newSocket.on('unread_notifications', (data) => {
      console.log('=== Socket.IO: Nhận thông báo chưa đọc ===');
      console.log('Số lượng:', data.length);
      console.log('Dữ liệu:', JSON.stringify(data, null, 2));
      
      // Cập nhật danh sách thông báo (nối thêm vào danh sách hiện tại)
      setNotifications(prev => {
        // Lọc ra các thông báo không trùng lặp
        const existingIds = new Set(prev.map(n => n._id));
        const newNotifications = data.filter(n => !existingIds.has(n._id));
        return [...prev, ...newNotifications];
      });
    });
    
    // Xử lý sự kiện 'new_notification' (được gửi từ API gateway khi thanh toán thành công)
    newSocket.on('new_notification', (data) => {
      console.log('=== Socket.IO: Nhận thông báo mới từ API Gateway ===');
      console.log('Loại thông báo:', data.type || 'không xác định');
      console.log('Nội dung:', data.content);
      console.log('Dữ liệu đầy đủ:', JSON.stringify(data, null, 2));
      
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
      setNotifications(prev => {
        // Kiểm tra xem thông báo đã tồn tại chưa
        const exists = prev.some(n => n._id === data._id);
        if (exists) return prev;
        return [data, ...prev];
      });
    });
    
    newSocket.on('notification', (data) => {
      console.log('=== Socket.IO: Nhận thông báo thông thường ===');
      console.log('Nội dung:', data.content);
      console.log('Dữ liệu đầy đủ:', JSON.stringify(data, null, 2));
      
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
    });

    newSocket.on('notification_marked_read', (data) => {
      console.log('=== Socket.IO: Thông báo đã được đánh dấu đã đọc ===');
      console.log('Chi tiết:', JSON.stringify(data, null, 2));
      
      // Cập nhật trạng thái thông báo trong danh sách
      if (data.notification_id) {
        setNotifications(prev => prev.map(n => 
          n._id === data.notification_id ? { ...n, status: 'read' } : n
        ));
      }
    });
    
    newSocket.on('error', (error) => {
      console.error('=== Socket.IO: Lỗi từ server ===');
      console.error('Chi tiết lỗi:', error);
      toast.error(error.message || 'Lỗi không xác định từ server');
    });
    
    // Lắng nghe tất cả các sự kiện khác
    newSocket.onAny((eventName, ...args) => {
      console.log(`=== Socket.IO: Sự kiện không xử lý: ${eventName} ===`);
      console.log('Dữ liệu nhận được:', JSON.stringify(args, null, 2));
      
      // Xử lý đặc biệt nếu có sự kiện không mong đợi liên quan đến thông báo
      if (eventName === 'new_notification') {
        console.log('=== QUAN TRỌNG: Đã phát hiện sự kiện new_notification bị bỏ qua ===');
        try {
          const data = args[0];
          if (data && data.content) {
            toast.info(`Sự kiện bị bỏ qua: ${data.content}`, {
              position: "top-right",
              autoClose: 5000,
            });
            
            // Thử thêm thông báo vào danh sách
            setNotifications(prev => {
              // Kiểm tra xem thông báo đã tồn tại chưa
              const exists = prev.some(n => n._id === data._id);
              if (exists) return prev;
              return [data, ...prev];
            });
          }
        } catch (e) {
          console.error('Lỗi khi xử lý sự kiện new_notification bị bỏ qua:', e);
        }
      }
    });

    // Đóng kết nối khi component unmount
    return () => {
      console.log('=== Socket.IO: Đóng kết nối ===');
      if (newSocket) {
        newSocket.off();
        newSocket.disconnect();
      }
    };
  }, [socketStatus === 'reconnecting']); // Thử kết nối lại khi trạng thái là reconnecting

  // Debug: Hiển thị thông báo trong console mỗi khi socketStatus thay đổi
  useEffect(() => {
    console.log('=== Socket.IO: Trạng thái kết nối thay đổi ===');
    console.log('Trạng thái hiện tại:', socketStatus);
  }, [socketStatus]);

  // Đánh dấu thông báo đã đọc
  const handleMarkAsRead = async (notificationId) => {
    try {
      console.log('=== Đánh dấu thông báo đã đọc ===');
      console.log('ID thông báo:', notificationId);
      
      // Gọi API để đánh dấu đã đọc
      await markNotificationAsRead(notificationId);
      
      // Cập nhật trạng thái trong context
      setNotifications(notifications.map(n => 
        n._id === notificationId ? { ...n, status: 'read' } : n
      ));
      
      // Gửi lệnh đánh dấu đã đọc qua Socket.IO nếu kết nối đang mở
      if (socket && socket.connected) {
        console.log('Gửi yêu cầu đánh dấu đã đọc qua Socket.IO');
        socket.emit('mark_read', {
          notification_id: notificationId
        });
      }
    } catch (error) {
      console.error('Lỗi khi đánh dấu thông báo đã đọc:', error);
    }
  };

  // Đảm bảo context luôn có giá trị mới nhất
  const contextValue = {
    notifications,
    loading,
    socketStatus,
    markAsRead: handleMarkAsRead,
    socket // Thêm socket vào context để các component khác có thể truy cập
  };

  return (
    <NotificationContext.Provider value={contextValue}>
      {children}
      <ToastContainer />
    </NotificationContext.Provider>
  );
};

export default NotificationProvider; 