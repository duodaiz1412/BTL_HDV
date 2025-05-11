import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getBookings } from '../services/api';

const Bookings = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchBookings = async () => {
      try {
        const response = await getBookings();
        setBookings(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch bookings');
        setLoading(false);
      }
    };

    fetchBookings();
  }, []);

  if (loading) return <div className="text-center p-8">Loading...</div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">My Bookings</h1>

      {bookings.length === 0 ? (
        <div className="text-center p-8">
          <p className="text-gray-500">No bookings found</p>
          <Link
            to="/"
            className="text-blue-500 hover:text-blue-600 mt-4 inline-block"
          >
            Browse Movies
          </Link>
        </div>
      ) : (
        <div className="grid gap-6">
          {bookings.map((booking) => (
            <div
              key={booking._id}
              className="bg-white rounded-lg shadow p-6"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-semibold mb-2">
                    {booking.movie_title}
                  </h2>
                  <p className="text-gray-600">
                    Showtime: {new Date(booking.showtime).toLocaleString()}
                  </p>
                </div>
                <span
                  className={`
                    px-3 py-1 rounded-full text-sm
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
              </div>

              <div className="mb-4">
                <p className="text-gray-600">
                  <span className="font-medium">Seats:</span>{' '}
                  {booking.seats.join(', ')}
                </p>
                <p className="text-gray-600">
                  <span className="font-medium">Total Amount:</span>{' '}
                  {booking.total_amount.toLocaleString()} VND
                </p>
              </div>

              <div className="flex justify-end">
                <Link
                  to={`/bookings/${booking._id}`}
                  className="text-blue-500 hover:text-blue-600"
                >
                  View Details
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Bookings; 