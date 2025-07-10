import React from 'react';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

interface ConnectionStatusProps {
  isConnected: boolean;
  onReconnect?: () => void;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ isConnected, onReconnect }) => {
  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center space-x-2 p-2 bg-gray-100 rounded-lg">
        {isConnected ? (
          <>
            <Wifi className="h-5 w-5 text-green-600" />
            <span className="text-sm font-medium text-gray-800">Connected</span>
          </>
        ) : (
          <>
            <WifiOff className="h-5 w-5 text-red-500" />
            <span className="text-sm font-medium text-gray-600">Disconnected</span>
          </>
        )}
      </div>
      
      {!isConnected && onReconnect && (
        <button
          onClick={onReconnect}
          className="flex items-center px-2 py-1 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors duration-200 text-xs font-semibold"
          title="Reconnect WebSocket"
        >
          <RefreshCw className="h-3 w-3" />
        </button>
      )}
    </div>
  );
};

export default ConnectionStatus; 