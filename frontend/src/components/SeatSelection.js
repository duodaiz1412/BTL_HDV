import React, { useState, useEffect } from 'react';
import { getSeats, checkSeats } from '../services/api';

const SeatSelection = ({ showtimeId, onSeatsSelected }) => {
  const [seats, setSeats] = useState([]);
  const [selectedSeats, setSelectedSeats] = useState([]);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchSeats = async () => {
      try {
        const response = await getSeats(showtimeId);
        setSeats(response.data);
      } catch (err) {
        setError('Không thể tải thông tin ghế');
      }
    };
    fetchSeats();
  }, [showtimeId]);

  const handleSeatClick = async (seat) => {
    if (seat.status === 'booked') return;

    const newSelectedSeats = selectedSeats.includes(seat.id)
      ? selectedSeats.filter(s => s !== seat.id)
      : [...selectedSeats, seat.id];

    setSelectedSeats(newSelectedSeats);

    try {
      if (newSelectedSeats.length > 0) {
        await checkSeats(showtimeId, newSelectedSeats);
        onSeatsSelected(newSelectedSeats);
      }
    } catch (err) {
      setError('Ghế đã được đặt');
      setSelectedSeats(selectedSeats.filter(s => s !== seat.id));
    }
  };

  return (
    <div className="p-4">
      <h3 className="text-xl font-semibold mb-4">Chọn ghế</h3>
      {error && <p className="text-red-500 mb-4">{error}</p>}
      <div className="grid grid-cols-8 gap-2">
        {seats.map((seat) => (
          <button
            key={seat.id}
            onClick={() => handleSeatClick(seat)}
            disabled={seat.status === 'booked'}
            className={`
              p-2 rounded text-center
              ${seat.status === 'booked' 
                ? 'bg-gray-300 cursor-not-allowed' 
                : selectedSeats.includes(seat.id)
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
              }
            `}
          >
            {seat.seat_number}
          </button>
        ))}
      </div>
      <div className="mt-4 flex gap-4">
        <div className="flex items-center">
          <div className="w-4 h-4 bg-gray-100 rounded mr-2"></div>
          <span>Ghế trống</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-gray-300 rounded mr-2"></div>
          <span>Đã đặt</span>
        </div>
        <div className="flex items-center">
          <div className="w-4 h-4 bg-blue-600 rounded mr-2"></div>
          <span>Đã chọn</span>
        </div>
      </div>
    </div>
  );
};

export default SeatSelection; 