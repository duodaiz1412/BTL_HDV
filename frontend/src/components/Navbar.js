import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useNotifications } from './NotificationProvider';

const Navbar = () => {
  const navigate = useNavigate();
  const customerId = localStorage.getItem('customer_id');
  const { unreadCount } = useNotifications();

  const handleLogout = () => {
    localStorage.removeItem('customer_id');
    navigate('/login');
  };

  return (
    <nav className="bg-gray-800 text-white p-4">
      <div className="container mx-auto flex justify-between items-center">
        <Link to="/" className="text-xl font-bold">
          Movie Booking
        </Link>
        <div className="flex items-center space-x-4">
          <Link to="/" className="hover:text-gray-300">
            Trang chủ
          </Link>
          {customerId ? (
            <>
              <Link to="/bookings" className="hover:text-gray-300">
                Đặt vé của tôi
              </Link>
              <Link to="/notifications" className="hover:text-gray-300 relative">
                Thông báo
                {unreadCount > 0 && (
                  <span className="absolute -top-1 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </Link>
              <Link to="/profile" className="hover:text-gray-300">
                Tài khoản
              </Link>
              <button
                onClick={handleLogout}
                className="hover:text-gray-300"
              >
                Đăng xuất
              </button>
            </>
          ) : (
            <Link to="/login" className="hover:text-gray-300">
              Đăng nhập
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar; 