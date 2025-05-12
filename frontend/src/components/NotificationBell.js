import React, { useState, useEffect } from 'react';
import { useNotifications } from './NotificationProvider';
import { markNotificationAsRead } from '../services/api';

const NotificationBell = () => {
  const { notifications, loading, socketStatus, markAsRead } = useNotifications();
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);

  // Đếm số thông báo chưa đọc
  useEffect(() => {
    if (notifications) {
      const count = notifications.filter(n => n.status === 'pending').length;
      setUnreadCount(count);
    }
  }, [notifications]);

  const toggleNotifications = () => {
    setIsOpen(!isOpen);
  };

  const handleNotificationClick = async (notification) => {
    try {
      if (notification._id && notification.status === 'pending') {
        // Gọi API để đánh dấu đã đọc
        await markNotificationAsRead(notification._id);
        
        // Cập nhật trạng thái trong context
        markAsRead(notification._id);
      }
    } catch (error) {
      console.error('Lỗi khi đánh dấu thông báo đã đọc:', error);
    }
  };

  // Xác định màu biểu tượng dựa trên trạng thái kết nối
  const getIconColor = () => {
    if (socketStatus === 'connected') {
      return 'text-gray-600 hover:text-blue-500';
    } else if (socketStatus.startsWith('error:') || socketStatus === 'reconnect failed') {
      return 'text-red-500 hover:text-red-400';
    } else if (socketStatus.startsWith('reconnecting')) {
      return 'text-yellow-500 hover:text-yellow-400';
    }
    return 'text-gray-400 hover:text-blue-400';
  };

  return (
    <div className="relative">
      <button 
        onClick={toggleNotifications} 
        className={`relative p-2 transition-colors ${getIconColor()}`}
        title={socketStatus === 'connected' ? 'Kết nối thông báo đang hoạt động' : `Trạng thái kết nối: ${socketStatus}`}
      >
        <svg 
          xmlns="http://www.w3.org/2000/svg" 
          fill="none" 
          viewBox="0 0 24 24" 
          stroke="currentColor" 
          className="w-6 h-6"
        >
          <path 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            strokeWidth={2} 
            d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" 
          />
        </svg>
        
        {unreadCount > 0 && (
          <span className="absolute top-1 right-1 inline-flex items-center justify-center px-2 py-1 text-xs font-bold leading-none text-white transform translate-x-1/2 -translate-y-1/2 bg-red-500 rounded-full">
            {unreadCount}
          </span>
        )}
      </button>
      
      {isOpen && (
        <div className="absolute right-0 mt-2 w-80 bg-white rounded-md shadow-lg overflow-hidden z-20 border border-gray-200">
          <div className="py-2 px-3 bg-gray-100 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h3 className="text-sm font-semibold text-gray-800">Thông báo</h3>
              <div className="flex items-center">
                {unreadCount > 0 && (
                  <span className="text-xs text-gray-500 mr-2">
                    {unreadCount} chưa đọc
                  </span>
                )}
                <span className={`w-2 h-2 rounded-full ${socketStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'}`}
                      title={socketStatus === 'connected' ? 'Đã kết nối' : socketStatus}>
                </span>
              </div>
            </div>
          </div>
          
          <div className="max-h-80 overflow-y-auto">
            {socketStatus.startsWith('error:') || socketStatus === 'reconnect failed' ? (
              <div className="px-4 py-3 text-center text-red-500 bg-red-50">
                <p>Không thể kết nối đến dịch vụ thông báo</p>
                <p className="text-xs mt-1">{socketStatus}</p>
              </div>
            ) : null}
            
            {loading ? (
              <div className="px-4 py-6 text-center text-gray-500">
                <p>Đang tải thông báo...</p>
              </div>
            ) : notifications.length > 0 ? (
              notifications.map((notification, index) => (
                <div 
                  key={index} 
                  className={`px-4 py-3 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${notification.status === 'pending' ? 'bg-blue-50' : ''}`}
                  onClick={() => handleNotificationClick(notification)}
                >
                  <p className="text-sm text-gray-800">{notification.content}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {notification.created_at 
                      ? new Date(notification.created_at).toLocaleString() 
                      : new Date().toLocaleString()}
                  </p>
                </div>
              ))
            ) : (
              <div className="px-4 py-6 text-center text-gray-500">
                <p>Không có thông báo mới</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationBell; 