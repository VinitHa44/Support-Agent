import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-toastify';
import DraftReviewPanel from '../components/DraftReviewPanel';
import ConnectionStatus from '../components/ConnectionStatus';
import { DraftData } from '../types/api';
import { RefreshCw } from 'lucide-react';

const DraftReviewPage: React.FC = () => {
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

  // Simplified useEffect for initialization
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
        
        // Only show important feedback, not verbose messages
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
          icon: icon || '/agent-logo.svg', // Use our custom logo as default
          tag: 'draft-review',
          silent: false,
          requireInteraction: true, // Keep notification until user interacts
        });

        notification.onclick = () => {
          window.focus();
          notification.close();
        };

        // Auto-close after 1 hour (3600000 ms) minimum as requested
        setTimeout(() => {
          notification.close();
        }, 3600000); // 1 hour
        
        console.log('Desktop notification sent successfully');
      } catch (error) {
        console.error('Failed to send notification:', error);
        // Fallback toast without verbose message
        toast.info('New draft received');
      }
    } else {
      console.log('Notification not available. Permission:', Notification.permission);
      // Fallback toast without verbose message
      toast.info('New draft received');
    }
  };

  const handleOpen = () => {
    setIsConnected(true);
    
    // Only show success toast if this was a reconnection
    const wasReconnecting = reconnectAttemptsRef.current > 0;
    
    reconnectAttemptsRef.current = 0; // Reset reconnection attempts
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
    
    // Only log abnormal closures for debugging
    if (event.code !== 1000) {
      console.log(`WebSocket closed abnormally. Code: ${event.code}`);
      scheduleReconnect();
    }
  };

  const handleError = (error: Event) => {
    console.error('WebSocket error occurred:', error);
    // Remove verbose toast error messages
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
      
      // Set a connection timeout
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
        console.log('New draft received');
        
        if (message.data && message.data.subject && message.data.from && message.data.drafts) {
          setDraftQueue(prevQueue => [...prevQueue, message.data]);
          
          // Send Chrome notification
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

  const currentDraft = draftQueue[currentDraftIndex];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 p-2 rounded-full mr-4">
                  <RefreshCw className="h-6 w-6 text-gray-500 dark:text-gray-400" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-800 dark:text-white">
                    AI Draft Review
                  </h1>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Review and approve AI-generated email responses.
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <ConnectionStatus isConnected={isConnected} onReconnect={manualReconnect} />
                
                {/* Notification Status */}
                <div className="flex items-center space-x-2 p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
                  <div className={`w-2 h-2 rounded-full ${
                    notificationPermission === 'granted' ? 'bg-green-500' : 
                    notificationPermission === 'denied' ? 'bg-red-500' : 'bg-yellow-500'
                  }`}></div>
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200">
                    {notificationPermission === 'granted' ? 'Notifications On' : 
                     notificationPermission === 'denied' ? 'Notifications Off' : 'Notifications Pending'}
                  </span>
                  {notificationPermission !== 'granted' && (
                    <button
                      onClick={requestNotificationPermission}
                      className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 rounded hover:bg-blue-200 dark:hover:bg-blue-800"
                    >
                      Enable
                                         </button>
                   )}
                 </div>
                 
                 {/* Test Connection Button */}
                 {isConnected && (
                   <button
                     onClick={testConnection}
                     className="px-3 py-2 text-sm font-medium bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-200 rounded-lg hover:bg-green-200 dark:hover:bg-green-800 transition-colors"
                   >
                     Test Connection
                   </button>
                 )}
              </div>
            </div>
          </div>

          {draftQueue.length > 0 ? (
            <div className="space-y-6">
              {/* Draft Navigation */}
              {draftQueue.length > 1 && (
                <div className="bg-white dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                        Draft {currentDraftIndex + 1} of {draftQueue.length}
                      </span>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => navigateToDraft(currentDraftIndex - 1)}
                          disabled={currentDraftIndex === 0}
                          className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                        >
                          ← Previous
                        </button>
                        <button
                          onClick={() => navigateToDraft(currentDraftIndex + 1)}
                          disabled={currentDraftIndex === draftQueue.length - 1}
                          className="px-3 py-1 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                        >
                          Next →
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      {draftQueue.map((_, index) => (
                        <button
                          key={index}
                          onClick={() => navigateToDraft(index)}
                          className={`w-3 h-3 rounded-full transition-colors duration-200 ${
                            index === currentDraftIndex
                              ? 'bg-blue-500'
                              : 'bg-gray-300 dark:bg-gray-600 hover:bg-gray-400 dark:hover:bg-gray-500'
                          }`}
                          title={`Go to draft ${index + 1}`}
                        />
                      ))}
                    </div>
                  </div>
                </div>
              )}
              
              <DraftReviewPanel
                draftData={currentDraft}
                onSend={sendDraftResponse}
                queueCount={draftQueue.length}
              />
            </div>
          ) : (
            <div className="text-center py-20 px-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
              <div className="bg-gray-100 dark:bg-gray-700 rounded-full p-5 w-24 h-24 mx-auto mb-6 flex items-center justify-center">
                <RefreshCw className="h-12 w-12 text-gray-400 dark:text-gray-500" />
              </div>
              <h2 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">
                Waiting for new drafts...
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400 max-w-sm mx-auto">
                When a new email is processed and requires your review, it will appear here automatically. Ensure your connection is active.
              </p>
              
              {/* Connection Debug Info */}
              <div className="mt-6 p-4 bg-gray-100 dark:bg-gray-700 rounded-lg text-left max-w-md mx-auto">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Connection Status</h3>
                <div className="space-y-1 text-xs text-gray-600 dark:text-gray-400">
                  <div>WebSocket: <span className={isConnected ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}>{isConnected ? 'Connected' : 'Disconnected'}</span></div>
                  <div>User ID: <span className="font-mono">{userId}</span></div>
                  <div>Notifications: <span className={notificationPermission === 'granted' ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}>{notificationPermission}</span></div>
                  <div>URL: <span className="font-mono text-xs break-all">{wsRef.current?.url || 'Not connected'}</span></div>
                </div>
              </div>
              
              {!isConnected && (
                <div className="mt-6">
                  <button
                    onClick={manualReconnect}
                    className="flex items-center mx-auto px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors duration-200 text-sm font-semibold border border-gray-200 dark:border-gray-600"
                  >
                    <RefreshCw size={14} className="mr-2" />
                    Attempt to Reconnect
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DraftReviewPage; 