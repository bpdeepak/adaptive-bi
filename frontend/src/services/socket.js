import { io } from 'socket.io-client';
import { API_CONFIG, SOCKET_EVENTS } from '../utils/constants';

class SocketService {
  constructor() {
    this.socket = null;
    this.listeners = {};
  }

  connect() {
    if (!this.socket) {
      this.socket = io(API_CONFIG.BACKEND_URL, {
        autoConnect: true,
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
        forceNew: true,
      });

      this.socket.on(SOCKET_EVENTS.CONNECT, () => {
        console.log('Socket connected');
      });

      this.socket.on(SOCKET_EVENTS.DISCONNECT, () => {
        console.log('Socket disconnected');
      });

      this.socket.on(SOCKET_EVENTS.ERROR, (error) => {
        console.error('Socket error:', error);
      });
    }
    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  on(event, callback) {
    if (this.socket) {
      this.socket.on(event, callback);
      
      // Store listener for cleanup
      if (!this.listeners[event]) {
        this.listeners[event] = [];
      }
      this.listeners[event].push(callback);
    }
  }

  off(event, callback) {
    if (this.socket) {
      this.socket.off(event, callback);
      
      // Remove from stored listeners
      if (this.listeners[event]) {
        this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
      }
    }
  }

  emit(event, data) {
    if (this.socket) {
      this.socket.emit(event, data);
    }
  }

  removeAllListeners() {
    if (this.socket) {
      Object.keys(this.listeners).forEach(event => {
        this.listeners[event].forEach(callback => {
          this.socket.off(event, callback);
        });
      });
      this.listeners = {};
    }
  }

  isConnected() {
    return this.socket && this.socket.connected;
  }
}

export const socketService = new SocketService();
