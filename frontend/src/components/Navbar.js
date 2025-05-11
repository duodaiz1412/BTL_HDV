import React from 'react';
import { Link, useNavigate } from 'react-router-dom';

const Navbar = () => {
  const navigate = useNavigate();
  const customerId = localStorage.getItem('customer_id');

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
        <div className="space-x-4">
          <Link to="/" className="hover:text-gray-300">
            Trang chủ
          </Link>
          {customerId ? (
            <>
              <Link to="/bookings" className="hover:text-gray-300">
                Đặt vé của tôi
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