let ws = null;

export const connectWebSocket = (gameId, user, onMessage) => {
  ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}/`);
  
  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    onMessage(data);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
};

export const sendWebSocketMessage = (message) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(message));
  }
};

export const closeWebSocket = () => {
  if (ws) {
    ws.close();
  }
};