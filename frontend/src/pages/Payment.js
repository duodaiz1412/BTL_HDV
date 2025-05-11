import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getBookingById, createPayment } from '../services/api';

const Payment = () => {
  const { bookingId } = useParams();
  const navigate = useNavigate();
  const [booking, setBooking] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState('credit_card');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    const fetchBookingDetails = async () => {
      try {
        const response = await getBookingById(bookingId);
        setBooking(response.data);
        setLoading(false);
      } catch (err) {
        console.error('Lỗi khi lấy thông tin đặt vé:', err);
        setError('Không thể tải thông tin đặt vé');
        setLoading(false);
      }
    };

    fetchBookingDetails();
  }, [bookingId]);

  const handlePaymentMethodChange = (e) => {
    setPaymentMethod(e.target.value);
  };

  const handlePayment = async () => {
    if (processing) return;

    setProcessing(true);
    try {
      const paymentData = {
        booking_id: bookingId,
        amount: booking.total_amount,
        payment_method: paymentMethod,
        status: 'pending'
      };

      const response = await createPayment(paymentData);
      console.log('Thanh toán thành công:', response.data);
      
      // Xóa movie_id và showtime_id khỏi localStorage vì đã hoàn tất đặt vé
      localStorage.removeItem('selected_movie_id');
      localStorage.removeItem('selected_showtime_id');
      
      // Chuyển đến trang xác nhận thanh toán
      navigate(`/bookings/${bookingId}/confirmation`);
    } catch (err) {
      console.error('Lỗi khi thanh toán:', err);
      setError('Không thể hoàn tất thanh toán. Vui lòng thử lại sau.');
    } finally {
      setProcessing(false);
    }
  };

  const handleCancel = () => {
    // Quay về trang chi tiết đặt vé
    navigate(`/bookings/${bookingId}`);
  };

  if (loading) return <div className="text-center p-8">Đang tải...</div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;
  if (!booking) return <div className="text-center p-8">Không tìm thấy thông tin đặt vé</div>;

  // Định dạng tiền tệ
  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('vi-VN', {
      style: 'currency',
      currency: 'VND'
    }).format(amount);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-6 text-center">Thanh toán</h1>

      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Thông tin đặt vé</h2>
          
          <div className="mb-4">
            <div className="flex justify-between mb-2">
              <span>Mã đặt vé:</span>
              <span className="font-medium">{booking._id || booking.id}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span>Phim:</span>
              <span className="font-medium">{booking.movie_title || 'Thông tin không có sẵn'}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span>Ghế:</span>
              <span className="font-medium">{booking.seats?.join(', ') || 'Thông tin không có sẵn'}</span>
            </div>
            <div className="flex justify-between mb-2">
              <span>Số lượng:</span>
              <span className="font-medium">{booking.seats?.length || 0}</span>
            </div>
            <div className="flex justify-between font-semibold text-blue-600">
              <span>Tổng tiền:</span>
              <span>{formatCurrency(booking.total_amount)}</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Phương thức thanh toán</h2>
          
          <div className="mb-4">
            <div className="flex items-center mb-3">
              <input
                type="radio"
                id="credit_card"
                name="payment_method"
                value="credit_card"
                checked={paymentMethod === 'credit_card'}
                onChange={handlePaymentMethodChange}
                className="mr-2"
              />
              <label htmlFor="credit_card" className="flex items-center">
                <span className="mr-2">Thẻ tín dụng/ghi nợ</span>
                <div className="flex gap-1">
                  <div className="w-10 h-6 bg-blue-500 rounded text-white text-xs flex items-center justify-center">VISA</div>
                  <div className="w-10 h-6 bg-red-500 rounded text-white text-xs flex items-center justify-center">MC</div>
                </div>
              </label>
            </div>
            
            <div className="flex items-center mb-3">
              <input
                type="radio"
                id="banking"
                name="payment_method"
                value="banking"
                checked={paymentMethod === 'banking'}
                onChange={handlePaymentMethodChange}
                className="mr-2"
              />
              <label htmlFor="banking">Chuyển khoản ngân hàng</label>
            </div>
            
            <div className="flex items-center">
              <input
                type="radio"
                id="momo"
                name="payment_method"
                value="momo"
                checked={paymentMethod === 'momo'}
                onChange={handlePaymentMethodChange}
                className="mr-2"
              />
              <label htmlFor="momo" className="flex items-center">
                <span className="mr-2">Ví MoMo</span>
                <div className="w-6 h-6 bg-pink-500 rounded-full"></div>
              </label>
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <button
            onClick={handleCancel}
            className="flex-1 py-3 px-4 bg-gray-300 hover:bg-gray-400 rounded font-medium"
          >
            Quay lại
          </button>
          <button
            onClick={handlePayment}
            disabled={processing}
            className={`
              flex-1 py-3 px-4 rounded text-white font-medium
              ${processing ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-500 hover:bg-blue-600'}
            `}
          >
            {processing ? 'Đang xử lý...' : 'Hoàn tất thanh toán'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Payment; 