import React from 'react';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

interface ConnectionStatusProps {
  isConnected: boolean;
  onReconnect?: () => void;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ isConnected, onReconnect }) => {
  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center space-x-2 p-2 bg-gray-100 dark:bg-gray-800 rounded-lg">
        {isConnected ? (
          <>
            <Wifi className="h-5 w-5 text-green-600 dark:text-green-500" />
            <span className="text-sm font-medium text-gray-800 dark:text-gray-200">Connected</span>
          </>
        ) : (
          <>
            <WifiOff className="h-5 w-5 text-red-500 dark:text-red-400" />
            <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Disconnected</span>
          </>
        )}
      </div>
      
      {!isConnected && onReconnect && (
        <button
          onClick={onReconnect}
          className="flex items-center px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-200 rounded-lg hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors duration-200 text-xs font-semibold"
          title="Reconnect WebSocket"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      )}
    </div>
  );
};

export default ConnectionStatus; 