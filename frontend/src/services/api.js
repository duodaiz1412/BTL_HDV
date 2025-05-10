import axios from 'axios';

const API_URL = 'http://localhost:8000';

// Movie APIs
export const getMovies = () => axios.get(`${API_URL}/movies`);
export const getMovie = (id) => axios.get(`${API_URL}/movies/${id}`);
export const getShowtimes = (movieId) => axios.get(`${API_URL}/showtimes/${movieId}`);

// Seat APIs
export const getSeats = (showtimeId) => axios.get(`${API_URL}/seats/showtime/${showtimeId}`);
export const checkSeats = (showtimeId, seats) => axios.post(`${API_URL}/seats/check`, { showtimeId, seats });

// Booking APIs
export const createBooking = (bookingData) => axios.post(`${API_URL}/bookings`, bookingData);
export const getCustomerBookings = (customerId) => axios.get(`${API_URL}/bookings/customer/${customerId}`);

// Payment APIs
export const createPayment = (paymentData) => axios.post(`${API_URL}/payments`, paymentData);
export const getBookingPayments = (bookingId) => axios.get(`${API_URL}/payments/booking/${bookingId}`); 