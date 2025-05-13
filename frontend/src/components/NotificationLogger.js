import React, { useState, useEffect, useRef } from 'react';
import { useNotifications } from './NotificationProvider';

const NotificationLogger = () => {
  const { socket, socketStatus } = useNotifications();
  const [logs, setLogs] = useState([]);
  const [isVisible, setIsVisible] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const logContainerRef = useRef(null);

  // Hàm thêm log mới
  const addLog = (type, message, data = null) => {
    const timestamp = new Date().toISOString();
    const newLog = {
      id: Date.now(),
      timestamp,
      type,
      message,
      data
    };
    setLogs(prevLogs => [newLog, ...prevLogs].slice(0, 100)); // Giới hạn số lượng log lưu trữ
  };

  // Xóa tất cả log
  const clearLogs = () => {
    setLogs([]);
  };

  // Định nghĩa các lắng nghe sự kiện Socket.IO
  useEffect(() => {
    if (socket) {
      // Lắng nghe sự kiện thông báo mới trực tiếp
      const handleNewNotification = (data) => {
        addLog('notification', `Nhận thông báo mới: ${data.content || 'Không có nội dung'}`, data);
      };

      // Thiết lập interceptor cho tất cả các sự kiện
      const originalOnPacket = socket.onpacket;
      socket.onpacket = function(packet) {
        if (packet.type === 2) { // type 2 là event
          const eventName = packet.data[0];
          const eventData = packet.data[1];
          
          // Ghi log chi tiết hơn cho các sự kiện quan trọng
          if (eventName === 'new_notification') {
            addLog('important', `NHẬN SỰ KIỆN THÔNG BÁO MỚI: ${eventData?.content || 'Không có nội dung'}`, {
              eventName,
              data: eventData,
              time: new Date().toISOString(),
              packetType: packet.type
            });
          } else {
            addLog('receive', `Nhận sự kiện: ${eventName}`, eventData);
          }
        }
        originalOnPacket.call(socket, packet);
      };

      // Lưu lại emit gốc
      const originalEmit = socket.emit;
      socket.emit = function(event, ...args) {
        addLog('send', `Gửi sự kiện: ${event}`, args[0] || null);
        return originalEmit.apply(socket, [event, ...args]);
      };

      // Thêm log khi kết nối thay đổi
      const handleConnect = () => {
        addLog('connection', 'Kết nối thành công đến API Gateway', { 
          socketId: socket.id,
          transport: socket.io.engine.transport.name,
          upgrades: socket.io.engine.transport.upgrades
        });
      };

      const handleDisconnect = (reason) => {
        addLog('connection', 'Ngắt kết nối từ API Gateway', { reason });
      };

      const handleError = (error) => {
        addLog('error', 'Lỗi kết nối Socket.IO', error);
      };

      // Lắng nghe các sự kiện cụ thể
      socket.on('connect', handleConnect);
      socket.on('disconnect', handleDisconnect);
      socket.on('connect_error', handleError);
      socket.on('new_notification', handleNewNotification);

      // Cleanup
      return () => {
        socket.onpacket = originalOnPacket;
        socket.emit = originalEmit;
        socket.off('connect', handleConnect);
        socket.off('disconnect', handleDisconnect);
        socket.off('connect_error', handleError);
        socket.off('new_notification', handleNewNotification);
      };
    }
  }, [socket]);

  // Hiển thị thông tin về trạng thái socket khi thay đổi
  useEffect(() => {
    addLog('status', `Trạng thái Socket.IO thay đổi: ${socketStatus}`);
  }, [socketStatus]);

  // Tự động cuộn đến log mới nhất
  useEffect(() => {
    if (logContainerRef.current && isVisible) {
      logContainerRef.current.scrollTop = 0;
    }
  }, [logs, isVisible]);

  // Format dữ liệu JSON để hiển thị
  const formatData = (data) => {
    if (!data) return null;
    try {
      return JSON.stringify(data, null, 2);
    } catch (e) {
      return String(data);
    }
  };

  // Lấy màu dựa trên loại log
  const getLogTypeColor = (type) => {
    switch (type) {
      case 'receive': return 'bg-blue-100 text-blue-800';
      case 'send': return 'bg-purple-100 text-purple-800';
      case 'error': return 'bg-red-100 text-red-800';
      case 'connection': return 'bg-green-100 text-green-800';
      case 'status': return 'bg-yellow-100 text-yellow-800';
      case 'notification': return 'bg-indigo-100 text-indigo-800';
      case 'important': return 'bg-red-50 border border-red-200 text-red-600';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  // Format thời gian hiển thị
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString() + '.' + date.getMilliseconds().toString().padStart(3, '0');
  };

  // Thử kết nối lại
  const handleReconnect = () => {
    if (socket) {
      addLog('connection', 'Đang thử kết nối lại...', null);
      socket.disconnect();
      socket.connect();
    }
  };

  // Kích thước container dựa vào trạng thái mở rộng
  const containerSize = isExpanded 
    ? "md:w-[800px] max-h-[600px]" 
    : "md:w-[600px] max-h-[400px]";

  return (
    <div className="fixed bottom-0 right-0 z-50">
      {isVisible ? (
        <div className={`bg-white shadow-lg border border-gray-200 rounded-t-lg w-full ${containerSize} flex flex-col`}>
          <div className="flex justify-between items-center p-2 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center">
              <h3 className="text-sm font-semibold">Socket.IO Log Monitor</h3>
              <span className={`ml-2 w-2 h-2 rounded-full ${socketStatus === 'connected' ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span className="ml-2 text-xs text-gray-600">{socketStatus}</span>
            </div>
            <div className="flex space-x-2">
              <button 
                onClick={handleReconnect}
                className="px-2 py-1 text-xs bg-blue-100 hover:bg-blue-200 rounded"
              >
                Kết nối lại
              </button>
              <button 
                onClick={() => setIsExpanded(!isExpanded)}
                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded"
              >
                {isExpanded ? 'Thu nhỏ' : 'Mở rộng'}
              </button>
              <button 
                onClick={clearLogs}
                className="px-2 py-1 text-xs bg-gray-200 hover:bg-gray-300 rounded"
              >
                Xóa log
              </button>
              <button 
                onClick={() => setIsVisible(false)}
                className="px-2 py-1 text-xs bg-red-100 hover:bg-red-200 rounded"
              >
                Đóng
              </button>
            </div>
          </div>
          
          <div className="p-2 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
            <div className="text-xs text-gray-500">
              <span className="inline-block w-3 h-3 rounded-full bg-blue-100 mr-1"></span>Nhận
              <span className="inline-block w-3 h-3 rounded-full bg-purple-100 mx-1 ml-3"></span>Gửi
              <span className="inline-block w-3 h-3 rounded-full bg-red-100 mx-1 ml-3"></span>Lỗi
              <span className="inline-block w-3 h-3 rounded-full bg-indigo-100 mx-1 ml-3"></span>Thông báo
            </div>
            <div className="text-xs text-gray-500">
              {logs.length} log, tối đa 100 mục
            </div>
          </div>
          
          <div 
            ref={logContainerRef}
            className="overflow-y-auto flex-1 p-2 space-y-2 flex flex-col-reverse"
          >
            {logs.map(log => (
              <div key={log.id} className={`p-2 rounded text-xs ${getLogTypeColor(log.type)}`}>
                <div className="flex justify-between mb-1">
                  <span className="font-mono">{formatTime(log.timestamp)}</span>
                  <span className="font-semibold uppercase text-[10px]">{log.type}</span>
                </div>
                <div>{log.message}</div>
                {log.data && (
                  <pre className="mt-1 whitespace-pre-wrap bg-white bg-opacity-50 rounded p-1 text-[10px] overflow-x-auto">
                    {formatData(log.data)}
                  </pre>
                )}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <button 
          onClick={() => setIsVisible(true)}
          className="bg-gray-800 text-white p-2 rounded-tl-lg shadow-lg hover:bg-gray-700 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M5 2a1 1 0 011 1v1h1a1 1 0 010 2H6v1a1 1 0 01-2 0V6H3a1 1 0 010-2h1V3a1 1 0 011-1zm0 10a1 1 0 011 1v1h1a1 1 0 110 2H6v1a1 1 0 11-2 0v-1H3a1 1 0 110-2h1v-1a1 1 0 011-1zm7-10a1 1 0 01.707.293l.707.707L15.414 4a1 1 0 111.414 1.414l-1.414 1.414-.707.707a1 1 0 01-1.414-1.414l.707-.707L13.414 4a1 1 0 01.293-.707z" clipRule="evenodd" />
          </svg>
        </button>
      )}
    </div>
  );
};

export default NotificationLogger; 