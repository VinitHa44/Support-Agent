import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BarChart3, MessageSquare, Activity } from 'lucide-react';

const Navigation: React.FC = () => {
  const location = useLocation();

  const navigationItems = [
    {
      path: '/',
      name: 'Draft Review',
      icon: MessageSquare,
      description: 'Review and approve email drafts'
    },
    {
      path: '/dashboard',
      name: 'Analytics Dashboard',
      icon: BarChart3,
      description: 'View analytics and statistics'
    }
  ];

  return (
    <nav className="bg-white border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center gap-3">
            <div className="bg-gray-800 p-2 rounded-lg">
              <Activity className="h-5 w-5 text-white" />
            </div>
            <h1 className="text-lg font-bold text-gray-800">
              Support Agent AI
            </h1>
          </div>

          {/* Navigation Links */}
          <div className="flex space-x-8">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center px-3 py-2 rounded-lg text-sm font-semibold transition-colors ${
                    isActive
                      ? 'bg-gray-100 text-gray-800'
                      : 'text-gray-500 hover:text-gray-800 hover:bg-gray-100'
                  }`}
                  title={item.description}
                >
                  <Icon className="h-4 w-4 mr-2" />
                  {item.name}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </nav>
  );
};

export default Navigation; 