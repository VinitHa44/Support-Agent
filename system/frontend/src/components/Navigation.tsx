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
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center">
            <Activity className="h-8 w-8 text-blue-600 mr-3" />
            <h1 className="text-xl font-bold text-gray-900">
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
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
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