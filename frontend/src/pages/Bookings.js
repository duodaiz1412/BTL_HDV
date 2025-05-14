import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getBookings } from '../services/api';
import { formatDateTime, toVietnamTime } from '../utils/dateUtils';

const Bookings = () => {
  const [bookings, setBookings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    const fetchBookings = async () => {
      try {
        const response = await getBookings();
        // Sắp xếp booking theo thời gian mới nhất
        const sortedBookings = response.data.sort((a, b) => 
          new Date(b.showtime) - new Date(a.showtime)
        );
        setBookings(sortedBookings);
        setLoading(false);
      } catch (err) {
        if (err.message === 'Customer ID not found') {
          setError('Bạn cần đăng nhập để xem thông tin đặt vé');
        } else {
          setError('Không thể tải thông tin đặt vé');
        }
        setLoading(false);
      }
    };

    fetchBookings();
  }, []);

  // Lọc booking theo tab đang active
  const filteredBookings = bookings.filter(booking => {
    if (activeTab === 'all') return true;
    if (activeTab === 'paid') return booking.status === 'paid';
    if (activeTab === 'pending') return booking.status === 'pending';
    return true;
  });

  if (loading) return <div className="text-center p-8">Loading...</div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Vé của tôi</h1>

      {/* Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('all')}
          className={`px-4 py-2 rounded-md ${
            activeTab === 'all'
              ? 'bg-white text-blue-600 shadow'
              : 'text-gray-600 hover:text-blue-600'
          }`}
        >
          Tất cả ({bookings.length})
        </button>
        <button
          onClick={() => setActiveTab('paid')}
          className={`px-4 py-2 rounded-md ${
            activeTab === 'paid'
              ? 'bg-white text-blue-600 shadow'
              : 'text-gray-600 hover:text-blue-600'
          }`}
        >
          Đã thanh toán ({bookings.filter(b => b.status === 'paid').length})
        </button>
        <button
          onClick={() => setActiveTab('pending')}
          className={`px-4 py-2 rounded-md ${
            activeTab === 'pending'
              ? 'bg-white text-blue-600 shadow'
              : 'text-gray-600 hover:text-blue-600'
          }`}
        >
          Chờ thanh toán ({bookings.filter(b => b.status === 'pending').length})
        </button>
      </div>

      {filteredBookings.length === 0 ? (
        <div className="text-center p-8">
          <p className="text-gray-500">Không tìm thấy đơn đặt vé nào</p>
          <Link
            to="/"
            className="text-blue-500 hover:text-blue-600 mt-4 inline-block"
          >
            Đặt vé xem phim
          </Link>
        </div>
      ) : (
        <div className="grid gap-6">
          {filteredBookings.map((booking) => (
            <div
              key={booking.id}
              className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow duration-200"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h2 className="text-xl font-semibold mb-2">
                    {booking.movie_title}
                  </h2>
                  <p className="text-gray-600">
                    Suất chiếu: {booking.showtime && booking.showtime !== 'Invalid Date' 
                      ? formatDateTime(booking.showtime)
                      : 'Không có thông tin'}
                  </p>
                </div>
                <span
                  className={`
                    px-3 py-1 rounded-full text-sm font-medium
                    ${booking.status === 'paid'
                      ? 'bg-green-100 text-green-800'
                      : booking.status === 'pending'
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }
                  `}
                >
                  {booking.status === 'paid' ? 'Đã thanh toán' : 
                   booking.status === 'pending' ? 'Chờ thanh toán' : 
                   booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
                </span>
              </div>

              <div className="mb-4">
                <p className="text-gray-600">
                  <span className="font-medium">Ghế:</span>{' '}
                  {Array.isArray(booking.seats)
                    ? booking.seats.map(seat => typeof seat === 'object' ? seat.seat_number : seat).join(', ')
                    : booking.seats
                  }
                </p>
                <p className="text-gray-600">
                  <span className="font-medium">Tổng tiền:</span>{' '}
                  {booking.total_amount.toLocaleString()} VND
                </p>
              </div>

              <div className="flex justify-end">
                {booking.status === 'pending' ? (
                  <Link
                    to={`/payment/${booking.id}`}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded transition-colors duration-200"
                  >
                    Thanh toán ngay
                  </Link>
                ) : (
                  <Link
                    to={`/bookings/${booking.id}`}
                    className="text-blue-500 hover:text-blue-600 transition-colors duration-200"
                  >
                    Xem chi tiết
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Bookings; 