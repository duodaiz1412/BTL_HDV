import React from 'react';
import { Link } from 'react-router-dom';

function Navbar() {
  return (
    <nav className="bg-white shadow-lg">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-xl font-bold text-gray-800">
            Movie Booking
          </Link>
          
          <div className="flex space-x-4">
            <Link to="/movies" className="text-gray-600 hover:text-gray-900">
              Movies
            </Link>
            <Link to="/bookings" className="text-gray-600 hover:text-gray-900">
              My Bookings
            </Link>
            <Link to="/login" className="text-gray-600 hover:text-gray-900">
              Login
            </Link>
            <Link to="/register" className="text-gray-600 hover:text-gray-900">
              Register
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar; 