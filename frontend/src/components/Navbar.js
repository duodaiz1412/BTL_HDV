import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useNotifications } from './NotificationProvider';
import NotificationDropdown from './NotificationDropdown';
import {
  HomeIcon,
  TicketIcon,
  UserCircleIcon,
  ArrowRightOnRectangleIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const Navbar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const customerId = localStorage.getItem('customer_id');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    localStorage.removeItem('customer_id');
    navigate('/login');
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  const navLinks = customerId ? [
    { path: '/', label: 'Trang chủ', icon: HomeIcon },
    { path: '/bookings', label: 'Đặt vé của tôi', icon: TicketIcon },
    { path: '/profile', label: 'Tài khoản', icon: UserCircleIcon },
  ] : [];

  return (
    <nav className="bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center space-x-2">
            <span className="text-2xl font-bold bg-white text-blue-600 px-2 py-1 rounded">MB</span>
            <span className="hidden md:block text-xl font-semibold">Movie Booking</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            {navLinks.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center px-4 py-2 rounded-lg transition-colors duration-200 ${
                  isActive(path)
                    ? 'bg-white/10 text-white'
                    : 'hover:bg-white/5 text-blue-50'
                }`}
              >
                <Icon className="w-5 h-5 mr-2" />
                {label}
              </Link>
            ))}
            
            {customerId && (
              <>
                <div className="px-2">
                  <NotificationDropdown />
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center px-4 py-2 rounded-lg hover:bg-white/5 text-blue-50 transition-colors duration-200"
                >
                  <ArrowRightOnRectangleIcon className="w-5 h-5 mr-2" />
                  Đăng xuất
                </button>
              </>
            )}

            {!customerId && (
              <Link
                to="/login"
                className="flex items-center px-6 py-2 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors duration-200"
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5 mr-2" />
                Đăng nhập
              </Link>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-white/5"
          >
            {isMobileMenuOpen ? (
              <XMarkIcon className="w-6 h-6" />
            ) : (
              <Bars3Icon className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden py-4 space-y-2">
            {navLinks.map(({ path, label, icon: Icon }) => (
              <Link
                key={path}
                to={path}
                className={`flex items-center px-4 py-3 rounded-lg transition-colors duration-200 ${
                  isActive(path)
                    ? 'bg-white/10 text-white'
                    : 'hover:bg-white/5 text-blue-50'
                }`}
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <Icon className="w-5 h-5 mr-3" />
                {label}
              </Link>
            ))}
            
            {customerId && (
              <>
                <div className="px-4 py-2">
                  <NotificationDropdown />
                </div>
                <button
                  onClick={() => {
                    handleLogout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="flex items-center w-full px-4 py-3 rounded-lg hover:bg-white/5 text-blue-50 transition-colors duration-200"
                >
                  <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
                  Đăng xuất
                </button>
              </>
            )}

            {!customerId && (
              <Link
                to="/login"
                className="flex items-center px-4 py-3 bg-white text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition-colors duration-200 mx-4"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5 mr-3" />
                Đăng nhập
              </Link>
            )}
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navbar; 