import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  LineChart,
  Line,
  Legend
} from 'recharts';
import { 
  Clock, 
  Mail, 
  Tag, 
  Users,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  X,
  Maximize2
} from 'lucide-react';
import { apiService } from '../services/api';
import { RequestLogStats, RequestLog } from '../types/api';
import { useDarkMode } from '../contexts/DarkModeContext';

const StatCard: React.FC<{ icon: React.ReactNode; title: string; value: string | number; }> = ({ icon, title, value }) => (
  <div className="bg-white dark:bg-gray-800 p-5 rounded-lg border border-gray-200 dark:border-gray-700 flex items-center">
    <div className="bg-gray-100 dark:bg-gray-700 p-3 rounded-full mr-4">
      {icon}
    </div>
    <div>
      <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{title}</p>
      <p className="text-2xl font-semibold text-gray-800 dark:text-white">{value}</p>
    </div>
  </div>
);

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<RequestLogStats | null>(null);
  const [recentLogs, setRecentLogs] = useState<RequestLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [selectedBody, setSelectedBody] = useState<string | null>(null);
  const [modalTitle, setModalTitle] = useState<string>('');
  const { isDarkMode } = useDarkMode();

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, logsData] = await Promise.all([
        apiService.getRequestStats(),
        apiService.getUserRequestLogs('default_user', 50)
      ]);
      
      setStats(statsData);
      setRecentLogs(logsData);
    } catch (error) {
      console.error('Dashboard data loading error:', error);
    } finally {
      setLoading(false);
    }
  };

  const toggleRowExpansion = (id: string) => {
    setExpandedRows(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const showBodyModal = (content: string, title: string = 'Content') => {
    setSelectedBody(content);
    setModalTitle(title);
  };

  const closeBodyModal = () => {
    setSelectedBody(null);
    setModalTitle('');
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-gray-800 dark:border-gray-200 mx-auto mb-4"></div>
          <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">Loading Dashboard...</h3>
          <p className="text-gray-600 dark:text-gray-400">Please wait while we fetch your data</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex items-center justify-center">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-8 text-center">
          <div className="bg-gray-200 dark:bg-gray-700 rounded-full p-4 w-16 h-16 mx-auto mb-4">
            <Mail className="h-8 w-8 text-gray-500 dark:text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold text-gray-800 dark:text-white mb-2">No Data Available</h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">We couldn't load your dashboard data. Please try refreshing.</p>
          <button 
            onClick={loadDashboardData}
            className="px-6 py-3 bg-gray-800 dark:bg-gray-200 text-white dark:text-gray-800 rounded-lg hover:bg-gray-900 dark:hover:bg-gray-300 transition-colors duration-150 font-medium"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const categoryData = stats.most_common_categories.slice(0, 10);
  
  const performanceData = recentLogs.slice(0, 20).map((log, index) => ({
    request: `#${index + 1}`,
    time: parseFloat(log.processing_time.toFixed(2)),
    reviewed: log.user_reviewed ? 1 : 0
  }));

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <div className="container mx-auto px-4 py-8">
        
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-800 dark:text-white">Support Analytics Dashboard</h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              An overview of your email support performance and trends.
            </p>
          </div>
          <button
            onClick={loadDashboardData}
            disabled={loading}
            className="flex items-center px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Refreshing...' : 'Refresh Data'}
          </button>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard icon={<Mail size={20} className="text-gray-500 dark:text-gray-400" />} title="Total Emails" value={stats.total_requests} />
          <StatCard icon={<Clock size={20} className="text-gray-500 dark:text-gray-400" />} title="Avg Response Time" value={`${stats.average_processing_time}s`} />
          <StatCard icon={<Users size={20} className="text-gray-500 dark:text-gray-400" />} title="Human Review Rate" value={`${stats.user_review_rate}%`} />
          <StatCard icon={<Tag size={20} className="text-gray-500 dark:text-gray-400" />} title="New Categories" value={stats.new_categories_created_count} />
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Most Common Categories */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Most Common Topics</h3>
            </div>
            <div style={{ height: '350px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDarkMode ? "#374151" : "#f0f0f0"} />
                  <XAxis 
                    dataKey="category" 
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval={0}
                    tick={{ fontSize: 12, fill: isDarkMode ? "#D1D5DB" : "#374151" }}
                  />
                  <YAxis tick={{ fontSize: 12, fill: isDarkMode ? "#D1D5DB" : "#374151" }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: isDarkMode ? '#1F2937' : 'white', 
                      border: `1px solid ${isDarkMode ? '#374151' : '#e5e5e5'}`,
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                      color: isDarkMode ? '#F3F4F6' : '#374151'
                    }}
                  />
                  <Bar dataKey="count" fill={isDarkMode ? "#9CA3AF" : "#4B5563"} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Performance over time */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <div className="flex items-center mb-4">
              <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Recent Request Performance</h3>
            </div>
            <div style={{ height: '350px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={isDarkMode ? "#374151" : "#f0f0f0"} />
                  <XAxis dataKey="request" tick={{ fontSize: 12, fill: isDarkMode ? "#D1D5DB" : "#374151" }} />
                  <YAxis tick={{ fontSize: 12, fill: isDarkMode ? "#D1D5DB" : "#374151" }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: isDarkMode ? '#1F2937' : 'white', 
                      border: `1px solid ${isDarkMode ? '#374151' : '#e5e5e5'}`,
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
                      color: isDarkMode ? '#F3F4F6' : '#374151'
                    }}
                  />
                  <Legend wrapperStyle={{ color: isDarkMode ? '#D1D5DB' : '#374151' }} />
                  <Line type="monotone" dataKey="time" stroke={isDarkMode ? "#9CA3AF" : "#4B5563"} name="Response Time (s)" />
                  <Line type="monotone" dataKey="reviewed" stroke={isDarkMode ? "#D1D5DB" : "#9CA3AF"} name="Reviewed" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
        
        {/* Recent Activity */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Recent Activity</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">Last 50 processed emails</p>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full bg-white dark:bg-gray-800 text-sm">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"></th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Timestamp</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Sender</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Response Time</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Reviewed</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {recentLogs.map((log) => (
                  <React.Fragment key={log.id}>
                    <tr 
                      className={`hover:bg-gray-50 dark:hover:bg-gray-700 ${expandedRows.has(log.id) ? 'bg-gray-50 dark:bg-gray-700' : ''}`}
                    >
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button onClick={() => toggleRowExpansion(log.id)} className="text-gray-600 dark:text-gray-300">
                          {expandedRows.has(log.id) ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
                        </button>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-300">
                        {new Date(log.timestamp).toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-300">{log.from_email}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-300">
                        <div className="flex flex-wrap gap-1">
                          {log.categories.map((cat, i) => (
                            <span key={i} className="px-2 py-0.5 rounded text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                              {cat}
                            </span>
                          ))}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-gray-700 dark:text-gray-300">{log.processing_time.toFixed(1)}s</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-0.5 text-xs font-semibold rounded-full ${
                          log.user_reviewed 
                            ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-800 dark:text-yellow-200'
                            : 'bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200'
                        }`}>
                          {log.user_reviewed ? 'Yes' : 'No'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap font-medium">
                        <button 
                          onClick={() => showBodyModal(log.draft_response, 'Final Response')}
                          className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100"
                        >
                          View
                        </button>
                      </td>
                    </tr>
                    {expandedRows.has(log.id) && (
                      <tr className="bg-gray-50 dark:bg-gray-700">
                        <td colSpan={7} className="px-6 py-4">
                          <div className="p-4 bg-white dark:bg-gray-800 rounded-md border border-gray-200 dark:border-gray-600">
                            <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-3">Request Details</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-4 gap-y-2 text-xs">
                              <div>
                                <strong className="text-gray-500 dark:text-gray-400">Request ID:</strong>
                                <span className="ml-2 text-gray-800 dark:text-gray-200 font-mono">{log.id}</span>
                              </div>
                              <div className="col-span-2">
                                <strong className="text-gray-500 dark:text-gray-400">Initial Request Body:</strong>
                                <div className="mt-1 p-2 border rounded-md bg-gray-50 dark:bg-gray-700 dark:border-gray-600 max-h-28 overflow-y-auto">
                                  <pre className="whitespace-pre-wrap font-sans text-gray-700 dark:text-gray-300">{log.body}</pre>
                                </div>
                                <button
                                  onClick={() => showBodyModal(log.body, 'Initial Request Body')}
                                  className="text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 mt-1"
                                >
                                  View Full
                                </button>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Modal for viewing full body */}
        {selectedBody && (
          <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center z-50 p-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
              <div className="flex justify-between items-center p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="text-lg font-semibold text-gray-800 dark:text-white">{modalTitle}</h3>
                <div className="flex items-center space-x-2">
                  <button onClick={closeBodyModal} className="text-gray-400 dark:text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
                    <X size={20} />
                  </button>
                </div>
              </div>
              <div className="p-6 overflow-y-auto">
                <pre className="whitespace-pre-wrap font-sans text-sm text-gray-700 dark:text-gray-300">{selectedBody}</pre>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 