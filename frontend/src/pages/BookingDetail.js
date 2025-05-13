import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getBookingById } from '../services/api';
import { ArrowLeftIcon, TicketIcon, ClockIcon, CurrencyDollarIcon, CalendarIcon, UserIcon } from '@heroicons/react/24/outline';
import { formatDistance } from 'date-fns';
import { vi } from 'date-fns/locale';

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
        setError('Không thể tải thông tin đặt vé');
        setLoading(false);
      }
    };

    fetchBookingDetails();
  }, [bookingId]);

  const formatTimeAgo = (date) => {
    try {
      return formatDistance(new Date(date), new Date(), {
        addSuffix: true,
        locale: vi
      });
    } catch (error) {
      return date;
    }
  };

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>
  );
  
  if (error) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center text-red-500 p-8">
        <p className="text-xl font-semibold mb-2">Đã có lỗi xảy ra</p>
        <p>{error}</p>
      </div>
    </div>
  );
  
  if (!booking) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center p-8">
        <p className="text-xl font-semibold mb-2">Không tìm thấy thông tin đặt vé</p>
        <Link to="/bookings" className="text-blue-500 hover:text-blue-600">
          Quay lại danh sách đặt vé
        </Link>
      </div>
    </div>
  );

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center mb-8">
          <Link
            to="/bookings"
            className="flex items-center text-gray-600 hover:text-blue-600 transition-colors duration-200"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Quay lại danh sách đặt vé
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-500 to-blue-600 p-6 text-white">
            <h1 className="text-3xl font-bold mb-2">{booking.movie_title}</h1>
            <div className="flex items-center space-x-4">
              <span className={`
                px-3 py-1 rounded-full text-sm font-medium text-white
                ${booking.status === 'paid' ? 'bg-green-600' :
                  booking.status === 'pending' ? 'bg-yellow-400' : 'bg-red-400'}
              `}>
                {booking.status === 'paid' ? 'Đã thanh toán' :
                 booking.status === 'pending' ? 'Chờ thanh toán' :
                 booking.status.charAt(0).toUpperCase() + booking.status.slice(1)}
              </span>
              <span className="text-sm opacity-75">Mã đặt vé: {booking._id}</span>
            </div>
          </div>

          {/* Main Content */}
          <div className="p-6">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Booking Details */}
              <div className="space-y-6">
                <h2 className="text-xl font-semibold mb-4">Thông tin đặt vé</h2>
                
                <div className="flex items-start space-x-3">
                  <ClockIcon className="w-6 h-6 text-gray-400 mt-1" />
                  <div>
                    <p className="font-medium">Suất chiếu</p>
                    <p className="text-gray-600">
                      {new Date(booking.showtime).toLocaleString('vi-VN', {
                        weekday: 'long',
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <TicketIcon className="w-6 h-6 text-gray-400 mt-1" />
                  <div>
                    <p className="font-medium">Ghế đã chọn</p>
                    <p className="text-gray-600">
                      {booking.seats.map(seat => seat.seat_number).join(', ')}
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <CurrencyDollarIcon className="w-6 h-6 text-gray-400 mt-1" />
                  <div>
                    <p className="font-medium">Tổng tiền</p>
                    <p className="text-gray-600">
                      {booking.total_amount.toLocaleString()} VND
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-3">
                  <CalendarIcon className="w-6 h-6 text-gray-400 mt-1" />
                  <div>
                    <p className="font-medium">Thời gian đặt vé</p>
                    <p className="text-gray-600">
                      {formatTimeAgo(booking.created_at)}
                    </p>
                  </div>
                </div>
              </div>

              {/* Payment Information */}
              {booking.payment && (
                <div className="space-y-6">
                  <h2 className="text-xl font-semibold mb-4">Thông tin thanh toán</h2>
                  
                  <div className="bg-gray-50 rounded-lg p-6 space-y-4">
                    <div>
                      <p className="font-medium">Mã thanh toán</p>
                      <p className="text-gray-600">{booking.payment._id}</p>
                    </div>

                    <div>
                      <p className="font-medium">Phương thức thanh toán</p>
                      <p className="text-gray-600">{booking.payment.payment_method}</p>
                    </div>

                    <div>
                      <p className="font-medium">Trạng thái</p>
                      <span className={`
                        inline-block px-3 py-1 rounded-full text-sm font-medium mt-1
                        ${booking.payment.status === 'completed' ? 'bg-green-100 text-green-800' :
                          booking.payment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'}
                      `}>
                        {booking.payment.status === 'completed' ? 'Hoàn thành' :
                         booking.payment.status === 'pending' ? 'Đang xử lý' :
                         booking.payment.status.charAt(0).toUpperCase() + booking.payment.status.slice(1)}
                      </span>
                    </div>

                    {booking.payment.paid_at && (
                      <div>
                        <p className="font-medium">Thời gian thanh toán</p>
                        <p className="text-gray-600">
                          {formatTimeAgo(booking.payment.paid_at)}
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Notifications */}
            {booking.notifications && booking.notifications.length > 0 && (
              <div className="mt-8">
                <h2 className="text-xl font-semibold mb-4">Lịch sử thông báo</h2>
                <div className="space-y-4">
                  {booking.notifications.map((notification) => (
                    <div
                      key={notification._id}
                      className="bg-gray-50 rounded-lg p-4 border border-gray-100"
                    >
                      <div className="flex items-start space-x-3">
                        <UserIcon className="w-5 h-5 text-gray-400 mt-1" />
                        <div className="flex-1">
                          <p className="text-gray-800">{notification.message}</p>
                          <p className="text-sm text-gray-500 mt-1">
                            {formatTimeAgo(notification.created_at)}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BookingDetail; 