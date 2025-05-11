import axios from 'axios';

const API_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Auth APIs
export const login = async (credentials) => {
  try {
    const response = await api.post('/auth/login', credentials);
    return response;
  } catch (error) {
    throw error;
  }
};

export const register = async (userData) => {
  try {
    const response = await api.post('/auth/register', userData);
    return response;
  } catch (error) {
    throw error;
  }
};

// Movie APIs
export const getMovies = () => api.get('/movies');
export const getMovieById = (id) => api.get(`/movies/${id}`);
export const getShowtimes = (movieId) => api.get(`/movies/${movieId}/showtimes`);

// Booking APIs
export const createBooking = async (bookingData) => {
  try {
    // Endpoint: POST /bookings
    // Request body: 
    // {
    //   "customer_id": "string",
    //   "movie_id": "string",
    //   "showtime_id": "string",
    //   "seats": ["string"],
    //   "total_amount": 0,
    //   "status": "pending"
    // }
    const response = await api.post('/bookings', bookingData);
    return response;
  } catch (error) {
    console.error('Error creating booking:', error);
    throw error;
  }
};

export const getBookings = () => api.get('/bookings');
export const getBookingById = (id) => api.get(`/bookings/${id}`);

// Payment APIs
export const createPayment = (paymentData) => api.post('/payments', paymentData);
export const getPayments = () => api.get('/payments');
export const getPaymentById = (id) => api.get(`/payments/${id}`);

// Seat APIs
export const getSeats = (showtimeId) => api.get(`/seats/showtime/${showtimeId}`);
export const bookSeats = (customer_id, movie_id, showtime_id, seats, total_amount, status) => api.post('/bookings', { customer_id, movie_id, showtime_id, seats, total_amount, status });

// Customer APIs
export const getProfile = () => {
  const customerId = localStorage.getItem('customer_id');
  if (!customerId) {
    throw new Error('Customer ID not found');
  }
  return api.get(`/customers/${customerId}`);
};

export const updateProfile = (data) => {
  const customerId = localStorage.getItem('customer_id');
  if (!customerId) {
    throw new Error('Customer ID not found');
  }
  return api.put(`/customers/${customerId}`, data);
};

export default api;