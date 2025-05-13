import React, { useState } from 'react';
import { markNotificationAsRead } from '../services/api';
import { useNotifications } from './NotificationProvider';
import { toast } from 'react-toastify';

const NotificationList = () => {
  const { notifications, setNotifications, updateUnreadCount } = useNotifications();
  const [markingAsRead, setMarkingAsRead] = useState(null);

  const handleMarkAsRead = async (notificationId) => {
    setMarkingAsRead(notificationId);
    try {
      await markNotificationAsRead(notificationId);
      const updatedNotifications = notifications.map(notification => 
        notification._id === notificationId 
          ? { ...notification, status: 'read' }
          : notification
      );
      setNotifications(updatedNotifications);
      updateUnreadCount(updatedNotifications);
    } catch (error) {
      console.error('Error marking notification as read:', error);
      toast.error('Không thể đánh dấu đã đọc');
    } finally {
      setMarkingAsRead(null);
    }
  };

  if (!notifications) {
    return <div className="text-center py-4">Đang tải thông báo...</div>;
  }

  return (
    <div className="max-w-lg mx-auto p-4">
      <h2 className="text-2xl font-bold mb-4">Thông báo</h2>
      {notifications.length === 0 ? (
        <p className="text-gray-500 text-center">Không có thông báo nào</p>
      ) : (
        <div className="space-y-4">
          {notifications.map((notification) => (
            <div
              key={notification._id}
              className={`p-4 rounded-lg shadow ${
                notification.status === 'unread'
                  ? 'bg-blue-50 border-l-4 border-blue-500'
                  : 'bg-white'
              }`}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <p className="text-gray-800">{notification.content}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {new Date(notification.created_at).toLocaleString()}
                  </p>
                </div>
                {notification.status === 'unread' && (
                  <button
                    onClick={() => handleMarkAsRead(notification._id)}
                    disabled={markingAsRead === notification._id}
                    className={`ml-4 text-sm ${
                      markingAsRead === notification._id
                        ? 'text-gray-400'
                        : 'text-blue-600 hover:text-blue-800'
                    }`}
                  >
                    {markingAsRead === notification._id ? 'Đang xử lý...' : 'Đánh dấu đã đọc'}
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default NotificationList; 