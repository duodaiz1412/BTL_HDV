import { io } from 'socket.io-client';

let socket = null;

export const getSocket = (customerId) => {
    if (socket && socket.connected) {
        return socket;
    }

    if (!customerId) {
        console.log('No customer_id provided, cannot initialize socket');
        return null;
    }

    socket = io('http://localhost:8000', {
        path: '/socket.io',
        transports: ['websocket', 'polling'],
        reconnectionAttempts: 10,
        reconnectionDelay: 1000,
        timeout: 20000,
        query: { customer_id: customerId },
    });

    return socket;
};

export const disconnectSocket = () => {
    if (socket) {
        socket.off();
        socket.disconnect();
        socket = null;
    }
};