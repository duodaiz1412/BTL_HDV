import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Home from './pages/Home';
import MovieDetail from './pages/MovieDetail';

const App = () => {
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <nav className="bg-white shadow-md">
          <div className="container mx-auto px-4">
            <div className="flex justify-between items-center h-16">
              <Link to="/" className="text-xl font-bold text-blue-600">
                Movie Booking
              </Link>
              <div className="flex space-x-4">
                <Link to="/" className="text-gray-600 hover:text-blue-600">
                  Trang chủ
                </Link>
                <Link to="/bookings" className="text-gray-600 hover:text-blue-600">
                  Đặt vé của tôi
                </Link>
              </div>
            </div>
          </div>
        </nav>

        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/movies/:id" element={<MovieDetail />} />
          </Routes>
        </main>

        <footer className="bg-white shadow-md mt-8">
          <div className="container mx-auto px-4 py-6">
            <p className="text-center text-gray-600">
              © 2024 Movie Booking System. All rights reserved.
            </p>
          </div>
        </footer>
      </div>
    </Router>
  );
};

export default App; 