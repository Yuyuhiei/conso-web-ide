// WebSocket service for real-time communication with the server

class WebSocketService {
  constructor(url = 'ws://localhost:5001/ws') {
    this.url = url;
    this.socket = null;
    this.isConnected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 2000; // 2 seconds
    this.listeners = {
      lexerResult: [],
      parserResult: [],
      error: [],
      open: [],
      close: []
    };
  }

  // Connect to the WebSocket server
  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      console.log('WebSocket is already connected or connecting');
      return;
    }

    try {
      this.socket = new WebSocket(this.url);

      this.socket.onopen = (event) => {
        console.log('WebSocket connected');
        this.isConnected = true;
        this.reconnectAttempts = 0;
        this.notifyListeners('open', event);
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle different message types
          switch (data.type) {
            case 'lexer_result':
              this.notifyListeners('lexerResult', data);
              break;
            case 'parser_result':
              this.notifyListeners('parserResult', data);
              break;
            case 'error':
              this.notifyListeners('error', data);
              break;
            default:
              console.warn('Unknown message type:', data.type);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onclose = (event) => {
        console.log('WebSocket disconnected');
        this.isConnected = false;
        this.notifyListeners('close', event);
        
        // Attempt to reconnect
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
          setTimeout(() => this.connect(), this.reconnectDelay);
        } else {
          console.error('Maximum reconnection attempts reached');
        }
      };

      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.notifyListeners('error', { message: 'WebSocket connection error' });
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  }

  // Send code to the server for real-time analysis
  sendCode(code) {
    if (!this.isConnected) {
      console.warn('WebSocket is not connected. Trying to reconnect...');
      this.connect();
      return;
    }

    try {
      const message = JSON.stringify({ code });
      this.socket.send(message);
    } catch (error) {
      console.error('Error sending message:', error);
    }
  }

  // Close the WebSocket connection
  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
      this.isConnected = false;
    }
  }

  // Add event listeners
  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    } else {
      console.warn(`Unknown event type: ${event}`);
    }
    return this; // Allow chaining
  }

  // Remove event listeners
  off(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(cb => cb !== callback);
    }
    return this; // Allow chaining
  }

  // Notify all listeners of a specific event
  notifyListeners(event, data) {
    if (this.listeners[event]) {
      this.listeners[event].forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} listener:`, error);
        }
      });
    }
  }
}

// Create and export a singleton instance
const websocketService = new WebSocketService();
export default websocketService;