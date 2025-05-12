import axios from 'axios';

const API_URL = 'http://localhost:8000';
const NOTIFICATION_SOCKET_URL = 'http://localhost:8007';

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
    //   "showtime": "string",
    //   "seats": [{ "seat_id": "string", "seat_number": "string" }],
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

export const getBookings = () => {
  const customerId = localStorage.getItem('customer_id');
  if (!customerId) {
    throw new Error('Customer ID not found');
  }
  return api.get(`/bookings/customer/${customerId}`);
};

export const getBookingById = (id) => api.get(`/bookings/${id}`);

// Payment APIs
export const createPayment = (paymentData) => api.post('/payments', paymentData);
export const getPayments = () => api.get('/payments');
export const getPaymentById = (id) => api.get(`/payments/${id}`);

// Seat APIs
export const getSeats = (showtimeId) => api.get(`/seats/showtime/${showtimeId}`);
export const checkSeats = (showtimeId, seatIds) => api.post(`/seats/check`, seatIds, {
  params: { showtime_id: showtimeId }
});
export const bookSeats = (customer_id, movie_id, showtime_id, showtime, seats, total_amount, status) => {
  // Chuyển đổi mảng seat_id thành mảng đối tượng {seat_id, seat_number}
  const formattedSeats = Array.isArray(seats) ? seats.map(seatId => {
    // Nếu seats đã là mảng đối tượng thì không cần chuyển đổi
    if (typeof seatId === 'object' && seatId.seat_id && seatId.seat_number) {
      return seatId;
    }
    // Nếu không tìm thấy thông tin về seat_number, trả về một giá trị mặc định
    return { seat_id: seatId, seat_number: seatId };
  }) : [];

  return api.post('/bookings', { 
    customer_id, 
    movie_id, 
    showtime_id, 
    showtime, 
    seats: formattedSeats, 
    total_amount, 
    status 
  });
};

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

// Notification APIs
export const getNotifications = () => {
  const customerId = localStorage.getItem('customer_id');
  if (!customerId) {
    throw new Error('Customer ID not found');
  }
  return api.get(`/notifications/customer/${customerId}`);
};

export const markNotificationAsRead = (notificationId) => {
  return api.put(`/notifications/${notificationId}/status`, null, {
    params: { status: 'read' }
  });
};

export default api;