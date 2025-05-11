import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getSeats, bookSeats, createBooking, createPayment } from '../services/api';

const Booking = () => {
  const { showtimeId } = useParams();
  const navigate = useNavigate();
  const [seats, setSeats] = useState([]);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchSeats = async () => {
      try {
        const response = await getSeats(showtimeId);
        setSeats(response.data);
        setLoading(false);
      } catch (err) {
        setError('Failed to fetch seats');
        setLoading(false);
      }
    };

    fetchSeats();
  }, [showtimeId]);

  const handleSeatClick = (seat) => {
    if (seat.status === 'booked') return;

    setSelectedSeats((prev) => {
      if (prev.includes(seat.seat_number)) {
        return prev.filter((s) => s !== seat.seat_number);
      }
      return [...prev, seat.seat_number];
    });
  };

  const handleBooking = async () => {
    if (selectedSeats.length === 0) {
      setError('Please select at least one seat');
      return;
    }

    try {
      // Book seats
      await bookSeats(showtimeId, selectedSeats);

      // Create booking
      const bookingData = {
        showtime_id: showtimeId,
        seats: selectedSeats,
        total_amount: selectedSeats.length * 1000, // Assuming 1000 per seat
        status: 'pending'
      };
      const bookingResponse = await createBooking(bookingData);

      // Create payment
      const paymentData = {
        booking_id: bookingResponse.data._id,
        amount: bookingResponse.data.total_amount,
        payment_method: 'credit_card',
        status: 'pending'
      };
      await createPayment(paymentData);

      // Redirect to booking confirmation
      navigate(`/bookings/${bookingResponse.data._id}`);
    } catch (err) {
      setError('Failed to create booking');
    }
  };

  if (loading) return <div className="text-center p-8">Loading...</div>;
  if (error) return <div className="text-center text-red-500 p-8">{error}</div>;

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Select Seats</h1>
      
      <div className="mb-8">
        <div className="grid grid-cols-8 gap-2">
          {seats.map((seat) => (
            <button
              key={seat._id}
              onClick={() => handleSeatClick(seat)}
              disabled={seat.status === 'booked'}
              className={`
                p-4 rounded text-center
                ${seat.status === 'booked'
                  ? 'bg-gray-300 cursor-not-allowed'
                  : selectedSeats.includes(seat.seat_number)
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-100 hover:bg-gray-200'
                }
              `}
            >
              {seat.seat_number}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-8">
        <h2 className="text-xl font-semibold mb-4">Selected Seats</h2>
        <p className="mb-4">
          {selectedSeats.length > 0
            ? selectedSeats.join(', ')
            : 'No seats selected'}
        </p>
        <p className="mb-4">
          Total: {selectedSeats.length * 1000} VND
        </p>
        <button
          onClick={handleBooking}
          disabled={selectedSeats.length === 0}
          className={`
            w-full py-3 rounded text-white
            ${selectedSeats.length === 0
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-500 hover:bg-blue-600'
            }
          `}
        >
          Proceed to Payment
        </button>
      </div>
    </div>
  );
};

export default Booking; 