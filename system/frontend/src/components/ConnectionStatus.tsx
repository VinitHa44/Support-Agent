import React from 'react';
import { Wifi, WifiOff } from 'lucide-react';

interface ConnectionStatusProps {
  isConnected: boolean;
}

const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ isConnected }) => {
  return (
    <div className="flex items-center space-x-2">
      <div className="flex items-center space-x-2">
        {isConnected ? (
          <>
            <Wifi className="h-5 w-5 text-green-500" />
            <span className="text-sm font-medium text-green-600">Connected</span>
            <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
          </>
        ) : (
          <>
            <WifiOff className="h-5 w-5 text-red-500" />
            <span className="text-sm font-medium text-red-600">Disconnected</span>
            <div className="h-2 w-2 bg-red-500 rounded-full"></div>
          </>
        )}
      </div>
    </div>
  );
};

export default ConnectionStatus; 