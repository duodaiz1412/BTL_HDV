import React, { useState, useRef, useEffect } from 'react';
import { useNotifications } from './NotificationProvider';
import { markNotificationAsRead } from '../services/api';
import { BellIcon, CheckIcon, CheckBadgeIcon } from '@heroicons/react/24/outline';
import moment from 'moment';
import { formatTimeAgo, formatDateTime } from '../utils/dateUtils';
import { toast } from 'react-toastify';

const NotificationDropdown = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const dropdownRef = useRef(null);
  const { notifications, unreadCount, setNotifications, updateUnreadCount } = useNotifications();

  // Sắp xếp thông báo theo thời gian mới nhất
  const sortedNotifications = [...notifications].sort((a, b) => 
    moment(b.created_at).valueOf() - moment(a.created_at).valueOf()
  );

  // Đóng dropdown khi click ra ngoài
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Xử lý đánh dấu đã đọc một thông báo
  const handleMarkAsRead = async (notificationId) => {
    try {
      setIsLoading(true);
      await markNotificationAsRead(notificationId);
      const updatedNotifications = notifications.map(notification => 
        notification._id === notificationId 
          ? { ...notification, status: 'read' }
          : notification
      );
      setNotifications(updatedNotifications);
      updateUnreadCount(updatedNotifications);
      toast.success('Đã đánh dấu thông báo là đã đọc');
    } catch (error) {
      console.error('Error marking notification as read:', error);
      toast.error('Không thể đánh dấu thông báo là đã đọc');
    } finally {
      setIsLoading(false);
    }
  };

  // Xử lý đánh dấu tất cả đã đọc
  const handleMarkAllAsRead = async () => {
    try {
      setIsLoading(true);
      const unreadNotifications = notifications.filter(n => n.status === 'unread');
      await Promise.all(unreadNotifications.map(n => markNotificationAsRead(n._id)));
      
      const updatedNotifications = notifications.map(notification => ({
        ...notification,
        status: 'read'
      }));
      setNotifications(updatedNotifications);
      updateUnreadCount(updatedNotifications);
      toast.success('Đã đánh dấu tất cả thông báo là đã đọc');
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      toast.error('Không thể đánh dấu tất cả thông báo là đã đọc');
    } finally {
      setIsLoading(false);
    }
  };

  // Định dạng thời gian
  const formatTime = (dateString) => {
    if (!dateString) return '';
    
    try {
      const date = moment(dateString);
      const now = moment();
      
      // Nếu thời gian trong tương lai
      if (date.isAfter(now)) {
        return formatDateTime(dateString);
      }
      
      // Nếu là ngày hôm nay hoặc ngày trước đó, sử dụng định dạng tương đối
      return formatTimeAgo(dateString);
    } catch (error) {
      console.error('Error formatting date:', error);
      return dateString;
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Bell Icon với Badge */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-2 rounded-full hover:bg-gray-700 relative transition-colors duration-200"
        title="Thông báo"
      >
        <BellIcon className="w-6 h-6" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center animate-pulse">
            {unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute right-0 mt-2 w-96 bg-white rounded-lg shadow-xl z-50 max-h-[80vh] overflow-y-auto transform opacity-100 scale-100 transition-all duration-200">
          <div className="p-4 border-b sticky top-0 bg-white z-10">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-semibold text-gray-800">
                Thông báo {unreadCount > 0 && `(${unreadCount})`}
              </h3>
              {unreadCount > 0 && (
                <button
                  onClick={handleMarkAllAsRead}
                  disabled={isLoading}
                  className="text-sm text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                >
                  <CheckBadgeIcon className="w-4 h-4" />
                  Đánh dấu tất cả đã đọc
                </button>
              )}
            </div>
          </div>

          <div className="divide-y">
            {sortedNotifications.length > 0 ? (
              sortedNotifications.map((notification) => (
                <div
                  key={notification._id}
                  className={`p-4 hover:bg-gray-50 transition-colors duration-200 ${
                    notification.status === 'unread' ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <p className="text-sm text-gray-800">{notification.content}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {formatTime(notification.created_at)}
                      </p>
                    </div>
                    {notification.status === 'unread' && (
                      <button
                        onClick={() => handleMarkAsRead(notification._id)}
                        disabled={isLoading}
                        className="ml-2 text-xs text-blue-600 hover:text-blue-800 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                      >
                        <CheckIcon className="w-4 h-4" />
                        Đã đọc
                      </button>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-gray-500">
                <BellIcon className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Không có thông báo nào</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationDropdown; 