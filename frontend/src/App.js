import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import Navbar from './components/Navbar';
import PrivateRoute from './components/PrivateRoute';
import NotificationList from './components/NotificationList';
import NotificationProvider from './components/NotificationProvider';
import Home from './pages/Home';
import MovieDetail from './pages/MovieDetail';
import Booking from './pages/Booking';
import Bookings from './pages/Bookings';
import BookingDetail from './pages/BookingDetail';
import Profile from './pages/Profile';
import Login from './pages/Login';
import Register from './pages/Register';
import SeatSelection from './pages/SeatSelection';
import Payment from './pages/Payment';

function App() {
  return (
    <Router>
      <NotificationProvider>
        <div className="min-h-screen bg-gray-100">
          <Navbar />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/movies/:movieId" element={<MovieDetail />} />
              <Route
                path="/seats/showtime/:showtimeId"
                element={
                  <PrivateRoute>
                    <SeatSelection />
                  </PrivateRoute>
                }
              />
              <Route
                path="/showtimes/:showtimeId/booking"
                element={
                  <PrivateRoute>
                    <Booking />
                  </PrivateRoute>
                }
              />
              <Route
                path="/bookings"
                element={
                  <PrivateRoute>
                    <Bookings />
                  </PrivateRoute>
                }
              />
              <Route
                path="/bookings/:bookingId"
                element={
                  <PrivateRoute>
                    <BookingDetail />
                  </PrivateRoute>
                }
              />
              <Route
                path="/profile"
                element={
                  <PrivateRoute>
                    <Profile />
                  </PrivateRoute>
                }
              />
              <Route
                path="/payment/:bookingId"
                element={
                  <PrivateRoute>
                    <Payment />
                  </PrivateRoute>
                }
              />
              <Route
                path="/bookings/:bookingId/confirmation"
                element={
                  <PrivateRoute>
                    <BookingDetail />
                  </PrivateRoute>
                }
              />
              <Route
                path="/notifications"
                element={
                  <PrivateRoute>
                    <NotificationList />
                  </PrivateRoute>
                }
              />
            </Routes>
          </main>
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
          />
        </div>
      </NotificationProvider>
    </Router>
  );
}

export default App; 