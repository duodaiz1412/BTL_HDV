import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getBookingById } from '../services/api';

const BookingDetail = () => {
  const { bookingId } = useParams();
  const [booking, setBooking] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBookingDetails = async () => {
      try {
        const response = await getBookingById(bookingId);
        setBooking(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch booking details');
        setLoading(false);
      }
    };

    fetchBookingDetails();
  }, [bookingId]);

  if (loading) return <div className="text-center p-8">Loading...</div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;
  if (!booking) return <div className="text-center p-8">Booking not found</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Booking Details</h1>
          <Link
            to="/bookings"
            className="text-blue-500 hover:text-blue-600"
          >
            Back to Bookings
          </Link>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="mb-6">
            <h2 className="text-2xl font-semibold mb-4">{booking.movie_title}</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-gray-600">
                  <span className="font-medium">Booking ID:</span>{' '}
                  {booking._id}
                </p>
                <p className="text-gray-600">
                  <span className="font-medium">Showtime:</span>{' '}
                  {new Date(booking.showtime).toLocaleString()}
                </p>
                <p className="text-gray-600">
                  <span className="font-medium">Seats:</span>{' '}
                  {booking.seats.join(', ')}
                </p>
              </div>
              <div>
                <p className="text-gray-600">
                  <span className="font-medium">Status:</span>{' '}
                  <span
                    className={`
                      px-2 py-1 rounded-full text-sm
                      ${booking.status === 'confirmed'
                        ? 'bg-green-100 text-green-800'
                        : booking.status === 'pending'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }
                    `}
                  >
                    {booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                  </span>
                </p>
                <p className="text-gray-600">
                  <span className="font-medium">Total Amount:</span>{' '}
                  {booking.total_amount.toLocaleString()} VND
                </p>
                <p className="text-gray-600">
                  <span className="font-medium">Created At:</span>{' '}
                  {new Date(booking.created_at).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          {booking.payment && (
            <div className="border-t pt-6">
              <h3 className="text-xl font-semibold mb-4">Payment Information</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-gray-600">
                    <span className="font-medium">Payment ID:</span>{' '}
                    {booking.payment._id}
                  </p>
                  <p className="text-gray-600">
                    <span className="font-medium">Payment Method:</span>{' '}
                    {booking.payment.payment_method}
                  </p>
                </div>
                <div>
                  <p className="text-gray-600">
                    <span className="font-medium">Payment Status:</span>{' '}
                    <span
                      className={`
                        px-2 py-1 rounded-full text-sm
                        ${booking.payment.status === 'completed'
                          ? 'bg-green-100 text-green-800'
                          : booking.payment.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : 'bg-red-100 text-red-800'
                        }
                      `}
                    >
                      {booking.payment.status.charAt(0).toUpperCase() + booking.payment.status.slice(1)}
                    </span>
                  </p>
                  <p className="text-gray-600">
                    <span className="font-medium">Paid At:</span>{' '}
                    {booking.payment.paid_at
                      ? new Date(booking.payment.paid_at).toLocaleString()
                      : 'Not paid yet'}
                  </p>
                </div>
              </div>
            </div>
          )}

          {booking.notifications && booking.notifications.length > 0 && (
            <div className="border-t pt-6 mt-6">
              <h3 className="text-xl font-semibold mb-4">Notifications</h3>
              <div className="space-y-4">
                {booking.notifications.map((notification) => (
                  <div
                    key={notification._id}
                    className="bg-gray-50 rounded p-4"
                  >
                    <p className="text-gray-800">{notification.message}</p>
                    <p className="text-sm text-gray-500 mt-2">
                      {new Date(notification.created_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BookingDetail; 