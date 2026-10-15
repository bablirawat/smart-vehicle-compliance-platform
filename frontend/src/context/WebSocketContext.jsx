import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { useSite } from './SiteContext';

const WebSocketContext = createContext(null);

export const WebSocketProvider = ({ children }) => {
  const { selectedSiteId } = useSite();
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimerRef = useRef(null);

  useEffect(() => {
    if (!selectedSiteId) return;

    const connect = () => {
      let wsUrl;
      const rawWs = import.meta.env.VITE_WS_URL || import.meta.env.VITE_API_URL;
      if (rawWs) {
        let cleanBase = rawWs.replace(/\/+$/, '');
        // Strip trailing path segments if full URL (/api/v1, /api, /ws) was provided
        cleanBase = cleanBase.replace(/\/api(\/v1)?$/, '').replace(/\/ws$/, '');
        if (cleanBase.startsWith('http://')) {
          cleanBase = cleanBase.replace(/^http:\/\//, 'ws://');
        } else if (cleanBase.startsWith('https://')) {
          cleanBase = cleanBase.replace(/^https:\/\//, 'wss://');
        } else if (!cleanBase.startsWith('ws://') && !cleanBase.startsWith('wss://')) {
          cleanBase = `wss://${cleanBase}`;
        }
        wsUrl = `${cleanBase}/ws/sites/${selectedSiteId}`;
      } else {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        wsUrl = `${protocol}//${host}/ws/sites/${selectedSiteId}`;
      }

      console.log(`Connecting WebSocket to: ${wsUrl}`);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      };

      ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          setLastEvent(parsed);
        } catch (e) {
          console.error('Failed to parse WS message:', e);
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected. Attempting reconnect in 3s...');
        setIsConnected(false);
        reconnectTimerRef.current = setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error('WebSocket error:', err);
        ws.close();
      };

      wsRef.current = ws;
    };

    connect();

    return () => {
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      if (wsRef.current) wsRef.current.close();
    };
  }, [selectedSiteId]);

  return (
    <WebSocketContext.Provider value={{ isConnected, lastEvent }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
