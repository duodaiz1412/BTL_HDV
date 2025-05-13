import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { toast } from 'react-toastify';
import socketService from '../services/socket';
import { getNotifications } from '../services/api';

// Tạo context cho notifications
export const NotificationContext = createContext({
  notifications: [],
  unreadCount: 0,
  markAsRead: () => {},
});

export const useNotifications = () => useContext(NotificationContext);

export const NotificationProvider = ({ children }) => {
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);

  // Cập nhật số lượng thông báo chưa đọc
  const updateUnreadCount = useCallback((notifs) => {
    const count = notifs.filter(n => n.status === 'unread').length;
    setUnreadCount(count);
  }, []);

  // Lấy danh sách thông báo
  const fetchNotifications = useCallback(async () => {
    try {
      const response = await getNotifications();
      const notifs = response.data;
      setNotifications(notifs);
      updateUnreadCount(notifs);
    } catch (error) {
      console.error('Error fetching notifications:', error);
      toast.error('Không thể tải thông báo');
    }
  }, [updateUnreadCount]);

  // Xử lý thông báo mới
  const handleNewNotification = useCallback((notification) => {
    console.log('Received new notification:', notification);
    setNotifications(prev => {
      const newNotifications = [notification, ...prev];
      updateUnreadCount(newNotifications);
      return newNotifications;
    });
    
    // Hiển thị toast thông báo
    toast.info(notification.content, {
      onClick: () => {
        // Có thể thêm xử lý khi click vào toast
        window.location.href = '/notifications';
      }
    });
  }, [updateUnreadCount]);

  // Thiết lập kết nối socket
  const setupSocket = useCallback(() => {
    const customerId = localStorage.getItem('customer_id');
    if (!customerId) return;

    try {
      const socket = socketService.connect(customerId);

      // Xử lý sự kiện kết nối thành công
      socket.on('connect', () => {
        console.log('Socket connected in NotificationProvider');
        setIsConnected(true);
        fetchNotifications(); // Lấy lại danh sách thông báo khi kết nối lại
      });

      // Xử lý sự kiện mất kết nối
      socket.on('disconnect', () => {
        console.log('Socket disconnected in NotificationProvider');
        setIsConnected(false);
      });

      // Đăng ký lắng nghe sự kiện thông báo mới
      socketService.onNewNotification(handleNewNotification);

      // Lấy danh sách thông báo ban đầu
      fetchNotifications();

      // Cleanup khi component unmount
      return () => {
        socket.off('connect');
        socket.off('disconnect');
        socketService.offNewNotification(handleNewNotification);
        socketService.disconnect();
      };
    } catch (error) {
      console.error('Socket setup error:', error);
      toast.error('Không thể kết nối đến server thông báo');
    }
  }, [fetchNotifications, handleNewNotification]);

  // Theo dõi thay đổi của customer_id
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'customer_id') {
        if (e.newValue) {
          setupSocket();
        } else {
          socketService.disconnect();
          setNotifications([]);
          setUnreadCount(0);
          setIsConnected(false);
        }
      }
    };

    // Lắng nghe sự kiện thay đổi localStorage
    window.addEventListener('storage', handleStorageChange);
    
    // Thiết lập kết nối ban đầu
    setupSocket();

    // Cleanup
    return () => {
      window.removeEventListener('storage', handleStorageChange);
      socketService.disconnect();
    };
  }, [setupSocket]);

  // Cung cấp context cho toàn bộ ứng dụng
  return (
    <NotificationContext.Provider
      value={{
        notifications,
        unreadCount,
        setNotifications,
        updateUnreadCount,
        isConnected
      }}
    >
      {children}
    </NotificationContext.Provider>
  );
};

export default NotificationProvider; 