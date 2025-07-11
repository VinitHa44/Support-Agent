import React, { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import { toast } from 'react-toastify';
import { DraftData } from '../types/api';

interface DraftContextType {
  isConnected: boolean;
  draftQueue: DraftData[];
  currentDraftIndex: number;
  notificationPermission: NotificationPermission;
  setCurrentDraftIndex: (index: number) => void;
  sendDraftResponse: (response: { is_skip: boolean; body: string }) => void;
  manualReconnect: () => void;
  testConnection: () => void;
  navigateToDraft: (index: number) => void;
  requestNotificationPermission: () => Promise<void>;
}

const DraftContext = createContext<DraftContextType | undefined>(undefined);

export const useDraft = () => {
  const context = useContext(DraftContext);
  if (context === undefined) {
    throw new Error('useDraft must be used within a DraftProvider');
  }
  return context;
};

interface DraftProviderProps {
  children: ReactNode;
}

export const DraftProvider: React.FC<DraftProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const [draftQueue, setDraftQueue] = useState<DraftData[]>([]);
  const [currentDraftIndex, setCurrentDraftIndex] = useState(0);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');
  
  const wsRef = useRef<WebSocket | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isConnectingRef = useRef(false);
  const userId = 'default_user';

  // Initialize on mount
  useEffect(() => {
    requestNotificationPermission();
    connectWebSocket();
    
    return () => {
      cleanup();
    };
  }, []);

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      try {
        const permission = await Notification.requestPermission();
        setNotificationPermission(permission);
        console.log('Notification permission:', permission);
        
        if (permission === 'denied') {
          toast.warn('Notifications blocked - you may miss draft alerts');
        }
      } catch (error) {
        console.error('Error requesting notification permission:', error);
        setNotificationPermission('denied');
      }
    } else {
      console.log('This browser does not support notifications');
    }
  };

  const cleanup = () => {
    // Clear intervals and timeouts
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    // Close websocket
    if (wsRef.current) {
      wsRef.current.removeEventListener('open', handleOpen);
      wsRef.current.removeEventListener('message', handleMessage);
      wsRef.current.removeEventListener('close', handleClose);
      wsRef.current.removeEventListener('error', handleError);
      wsRef.current.close();
      wsRef.current = null;
    }
    
    isConnectingRef.current = false;
  };

  const startHeartbeat = () => {
    // Clear any existing heartbeat
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }
    
    // Send ping every 30 seconds to keep connection alive
    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000);
  };

  const stopHeartbeat = () => {
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  };

  const getReconnectDelay = (attempt: number) => {
    // Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
    return Math.min(1000 * Math.pow(2, attempt), 30000);
  };

  const sendChromeNotification = (title: string, body: string, icon?: string) => {
    console.log('Attempting to send Chrome notification. Permission:', Notification.permission);
    
    if ('Notification' in window && Notification.permission === 'granted') {
      try {
        const notification = new Notification(title, {
          body,
          icon: icon || '/agent-logo.svg',
          tag: 'draft-review',
          silent: false,
          requireInteraction: true,
        });

        notification.onclick = () => {
          window.focus();
          // Navigate to draft page when notification is clicked
          window.location.hash = '/';
          notification.close();
        };

        // Auto-close after 1 hour
        setTimeout(() => {
          notification.close();
        }, 3600000);
        
        console.log('Desktop notification sent successfully');
      } catch (error) {
        console.error('Failed to send notification:', error);
        toast.info('New draft received');
      }
    } else {
      console.log('Notification not available. Permission:', Notification.permission);
      toast.info('New draft received');
    }
  };

  const handleOpen = () => {
    setIsConnected(true);
    
    const wasReconnecting = reconnectAttemptsRef.current > 0;
    
    reconnectAttemptsRef.current = 0;
    isConnectingRef.current = false;
    startHeartbeat();
    
    if (wasReconnecting) {
      toast.success('Reconnected to draft service');
    }
  };

  const handleMessage = (event: MessageEvent) => {
    try {
      const message = JSON.parse(event.data);
      handleWebSocketMessage(message);
    } catch (error) {
      console.error('Failed to parse WebSocket message:', error);
      console.error('Raw message:', event.data);
    }
  };

  const handleClose = (event: CloseEvent) => {
    setIsConnected(false);
    isConnectingRef.current = false;
    stopHeartbeat();
    
    if (event.code !== 1000) {
      console.log(`WebSocket closed abnormally. Code: ${event.code}`);
      scheduleReconnect();
    }
  };

  const handleError = (error: Event) => {
    console.error('WebSocket error occurred:', error);
  };

  const connectWebSocket = () => {
    if (isConnectingRef.current) {
      return;
    }

    isConnectingRef.current = true;
    cleanup();

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const backendHost = window.location.hostname + ':8000';
    const wsUrl = `${protocol}//${backendHost}/api/v1/ws/drafts?user_id=${userId}`;
    
    console.log(`Connecting to WebSocket: ${wsUrl}`);
    
    try {
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.addEventListener('open', handleOpen);
      wsRef.current.addEventListener('message', handleMessage);
      wsRef.current.addEventListener('close', handleClose);
      wsRef.current.addEventListener('error', handleError);
      
      const connectionTimeout = setTimeout(() => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.CONNECTING) {
          console.log('WebSocket connection timed out');
          wsRef.current.close();
        }
      }, 30000);

      wsRef.current.addEventListener('open', () => clearTimeout(connectionTimeout));
    } catch (error) {
      console.error('Failed to create WebSocket:', error);
      isConnectingRef.current = false;
      scheduleReconnect();
    }
  };

  const scheduleReconnect = () => {
    if (isConnectingRef.current || reconnectAttemptsRef.current >= 10) {
      if (reconnectAttemptsRef.current >= 10) {
        console.log('Max reconnection attempts reached');
        toast.error('Connection failed. Please refresh the page.');
      }
      return;
    }

    const delay = getReconnectDelay(reconnectAttemptsRef.current);
    reconnectAttemptsRef.current++;
    
    console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current})`);
    
    reconnectTimeoutRef.current = setTimeout(() => {
      if (!isConnected && !isConnectingRef.current) {
        connectWebSocket();
      }
    }, delay);
  };

  const handleWebSocketMessage = (message: any) => {
    switch (message.type) {
      case 'draft_review':
        console.log('New draft received globally');
        
        if (message.data && message.data.subject && message.data.from && message.data.drafts) {
          setDraftQueue(prevQueue => [...prevQueue, message.data]);
          
          // Send Chrome notification regardless of current page
          sendChromeNotification(
            'New Draft Ready for Review',
            `Subject: ${message.data.subject}\nFrom: ${message.data.from}`
          );
          
        } else {
          console.error('Invalid draft data received:', message.data);
          toast.error('Received invalid draft data');
        }
        break;
        
      case 'pong':
        // Silent heartbeat response
        break;
        
      case 'connection_test_response':
        console.log('Connection test successful');
        toast.success('Connection test successful');
        break;
        
      case 'error':
        console.error('Server error:', message.data?.message || 'Unknown error');
        toast.error(`Server error: ${message.data?.message || 'Unknown error'}`);
        break;
        
      default:
        console.log('Unknown message type:', message.type);
        break;
    }
  };

  const sendDraftResponse = (response: { is_skip: boolean; body: string }) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (draftQueue.length === 0) {
        toast.warn("No active draft to respond to");
        return;
      }
      try {
        wsRef.current.send(JSON.stringify({
          type: 'draft_response',
          data: {
            is_skip: response.is_skip,
            body: response.body
          }
        }));
        
        // Remove the current draft and reset index if needed
        setDraftQueue(prevQueue => {
          const newQueue = prevQueue.filter((_, index) => index !== currentDraftIndex);
          // Adjust current index if necessary
          if (currentDraftIndex >= newQueue.length && newQueue.length > 0) {
            setCurrentDraftIndex(newQueue.length - 1);
          } else if (newQueue.length === 0) {
            setCurrentDraftIndex(0);
          }
          return newQueue;
        });
        
        const message = response.is_skip 
          ? 'Draft cancelled' 
          : 'Draft response sent';
        toast.success(message);
      } catch (error) {
        toast.error('Failed to send response');
        console.error('Send error:', error);
      }
    } else {
      toast.error('Not connected to server');
    }
  };

  const manualReconnect = () => {
    console.log('Manual reconnection initiated...');
    reconnectAttemptsRef.current = 0;
    cleanup();
    connectWebSocket();
  };

  const testConnection = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const testMessage = {
        type: 'connection_test',
        timestamp: new Date().toISOString(),
        user_id: userId
      };
      
      wsRef.current.send(JSON.stringify(testMessage));
      console.log('Sent connection test');
    } else {
      console.log('Cannot test connection - WebSocket not open');
      toast.error('Not connected to server');
    }
  };

  const navigateToDraft = (index: number) => {
    if (index >= 0 && index < draftQueue.length) {
      setCurrentDraftIndex(index);
    }
  };

  const value: DraftContextType = {
    isConnected,
    draftQueue,
    currentDraftIndex,
    notificationPermission,
    setCurrentDraftIndex,
    sendDraftResponse,
    manualReconnect,
    testConnection,
    navigateToDraft,
    requestNotificationPermission,
  };

  return (
    <DraftContext.Provider value={value}>
      {children}
    </DraftContext.Provider>
  );
}; 