import React from 'react';
import { Navigate } from 'react-router-dom';

const PrivateRoute = ({ children }) => {
  const customerId = localStorage.getItem('customer_id');
  
  if (!customerId) {
    // Chuyển hướng đến trang đăng nhập nếu chưa đăng nhập
    return <Navigate to="/login" />;
  }

  return children;
};

export default PrivateRoute; 