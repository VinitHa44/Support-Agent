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

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<RequestLogStats | null>(null);
  const [recentLogs, setRecentLogs] = useState<RequestLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());
  const [selectedBody, setSelectedBody] = useState<string | null>(null);
  const [modalTitle, setModalTitle] = useState<string>('');
  const [dateRange, setDateRange] = useState({
    startDate: '',
    endDate: ''
  });

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, logsData] = await Promise.all([
        apiService.getRequestStats(dateRange.startDate, dateRange.endDate),
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

  const handleDateRangeChange = (field: string, value: string) => {
    setDateRange(prev => ({ ...prev, [field]: value }));
  };

  const applyDateFilter = () => {
    loadDashboardData();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center max-w-md">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">Loading Dashboard...</h3>
          <p className="text-gray-600">Please wait while we fetch your data</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="bg-white rounded-2xl shadow-xl p-8 text-center max-w-md">
          <div className="bg-gray-100 rounded-full p-4 w-16 h-16 mx-auto mb-4">
            <Mail className="h-8 w-8 text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold text-gray-900 mb-2">No Data Available</h3>
          <p className="text-gray-600 mb-6">We couldn't load your dashboard data. Please try refreshing.</p>
          <button 
            onClick={loadDashboardData}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-150 font-medium"
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
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-bold text-gray-900 mb-2">📊 Support Analytics</h1>
                <p className="text-gray-600 text-lg">Monitor your email support performance and trends</p>
              </div>
              <button
                onClick={loadDashboardData}
                disabled={loading}
                className="flex items-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-all duration-200 shadow-md hover:shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <RefreshCw className={`h-5 w-5 mr-2 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Refreshing...' : 'Refresh Data'}
              </button>
            </div>
          </div>

          {/* Date Range Filter */}
          <div className="bg-white rounded-xl shadow-md p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📅 Filter by Date Range</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Start Date</label>
                <input
                  type="date"
                  value={dateRange.startDate}
                  onChange={(e) => handleDateRangeChange('startDate', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">End Date</label>
                <input
                  type="date"
                  value={dateRange.endDate}
                  onChange={(e) => handleDateRangeChange('endDate', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={applyDateFilter}
                  className="w-full px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all duration-200 shadow-md hover:shadow-lg font-medium"
                >
                  Apply Filter
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-blue-500 hover:shadow-xl transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Total Emails</p>
                <p className="text-3xl font-bold text-blue-600">{stats.total_requests}</p>
              </div>
              <div className="bg-blue-100 p-3 rounded-full">
                <Mail className="h-8 w-8 text-blue-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-green-500 hover:shadow-xl transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Avg Response Time</p>
                <p className="text-3xl font-bold text-green-600">{stats.average_processing_time}s</p>
              </div>
              <div className="bg-green-100 p-3 rounded-full">
                <Clock className="h-8 w-8 text-green-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-purple-500 hover:shadow-xl transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Human Review Rate</p>
                <p className="text-3xl font-bold text-purple-600">{stats.user_review_rate}%</p>
              </div>
              <div className="bg-purple-100 p-3 rounded-full">
                <Users className="h-8 w-8 text-purple-600" />
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border-l-4 border-orange-500 hover:shadow-xl transition-shadow duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">New Categories</p>
                <p className="text-3xl font-bold text-orange-600">{stats.new_categories_created_count}</p>
              </div>
              <div className="bg-orange-100 p-3 rounded-full">
                <Tag className="h-8 w-8 text-orange-600" />
              </div>
            </div>
          </div>
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Most Common Categories */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center mb-6">
              <div className="bg-blue-100 p-2 rounded-lg mr-3">
                <Tag className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">📋 Most Common Email Topics</h3>
                <p className="text-gray-600 text-sm">Top categories your customers write about</p>
              </div>
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={categoryData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="category" 
                    angle={-45}
                    textAnchor="end"
                    height={100}
                    interval={0}
                    tick={{ fontSize: 12 }}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e5e5',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                  <Bar dataKey="count" fill="#3B82F6" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Processing Time Trend */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <div className="flex items-center mb-6">
              <div className="bg-green-100 p-2 rounded-lg mr-3">
                <Clock className="h-6 w-6 text-green-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">⚡ Response Time Trend</h3>
                <p className="text-gray-600 text-sm">How fast we're responding to emails</p>
              </div>
            </div>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={performanceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="request" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: 'white', 
                      border: '1px solid #e5e5e5',
                      borderRadius: '8px',
                      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                    }}
                  />
                  <Legend />
                  <Line 
                    type="monotone" 
                    dataKey="time" 
                    stroke="#10B981" 
                    strokeWidth={3}
                    name="Response Time (seconds)"
                    dot={{ fill: '#10B981', strokeWidth: 2, r: 4 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Recent Requests Table */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-gray-50 to-gray-100 px-6 py-4 border-b border-gray-200">
            <div className="flex items-center">
              <div className="bg-indigo-100 p-2 rounded-lg mr-3">
                <Mail className="h-6 w-6 text-indigo-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-gray-900">📧 Recent Email Requests</h3>
                <p className="text-gray-600 text-sm">Latest customer emails and AI responses</p>
              </div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    👤 From
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    ✉️ Subject
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    🏷️ Categories
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    📝 Original Email
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    🤖 AI Response
                  </th>
                  <th className="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">
                    ⏱️ Response Time
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {recentLogs.slice(0, 10).map((log, index) => (
                  <tr key={log.id} className={`hover:bg-blue-50 transition-colors duration-150 ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="bg-blue-100 p-2 rounded-full mr-3">
                          <Mail className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-900">{log.from_email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <button
                          onClick={() => toggleRowExpansion(`subject-${log.id}`)}
                          className="flex items-center text-left bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded-lg transition-colors duration-150"
                        >
                          {expandedRows.has(`subject-${log.id}`) ? (
                            <ChevronDown className="h-4 w-4 mr-2 text-gray-600" />
                          ) : (
                            <ChevronRight className="h-4 w-4 mr-2 text-gray-600" />
                          )}
                          <span className="text-sm font-medium text-gray-900 max-w-xs truncate">
                            {expandedRows.has(`subject-${log.id}`) ? log.subject : `${log.subject.substring(0, 30)}...`}
                          </span>
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <button
                          onClick={() => toggleRowExpansion(`categories-${log.id}`)}
                          className="flex items-center text-left bg-gray-100 hover:bg-gray-200 px-3 py-2 rounded-lg transition-colors duration-150"
                        >
                          {expandedRows.has(`categories-${log.id}`) ? (
                            <ChevronDown className="h-4 w-4 mr-2 text-gray-600" />
                          ) : (
                            <ChevronRight className="h-4 w-4 mr-2 text-gray-600" />
                          )}
                          <div className="flex flex-wrap gap-1">
                            {expandedRows.has(`categories-${log.id}`) ? (
                              log.categories.map((category, index) => (
                                <span 
                                  key={index}
                                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                                >
                                  {category}
                                </span>
                              ))
                            ) : (
                              <>
                                {log.categories.slice(0, 1).map((category, index) => (
                                  <span 
                                    key={index}
                                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                                  >
                                    {category}
                                  </span>
                                ))}
                                {log.categories.length > 1 && (
                                  <span className="text-xs text-gray-500 font-medium">+{log.categories.length - 1} more</span>
                                )}
                              </>
                            )}
                          </div>
                        </button>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => showBodyModal(log.body, '📝 Original Email')}
                        className="flex items-center bg-blue-100 hover:bg-blue-200 text-blue-700 px-4 py-2 rounded-lg transition-colors duration-150 font-medium"
                      >
                        <Maximize2 className="h-4 w-4 mr-2" />
                        <span className="text-sm">Read Email</span>
                      </button>
                    </td>
                    <td className="px-6 py-4">
                      <button
                        onClick={() => showBodyModal(log.draft_response, '🤖 AI Generated Response')}
                        className="flex items-center bg-green-100 hover:bg-green-200 text-green-700 px-4 py-2 rounded-lg transition-colors duration-150 font-medium"
                      >
                        <Maximize2 className="h-4 w-4 mr-2" />
                        <span className="text-sm">View Response</span>
                      </button>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <Clock className="h-4 w-4 text-gray-400 mr-2" />
                        <span className="text-sm font-medium text-gray-900">{log.processing_time.toFixed(1)}s</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Content Modal */}
        {selectedBody && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-2xl max-w-4xl max-h-[85vh] w-full flex flex-col shadow-2xl">
              <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-t-2xl">
                <h3 className="text-xl font-bold text-gray-900">{modalTitle}</h3>
                <button
                  onClick={closeBodyModal}
                  className="text-gray-400 hover:text-gray-600 hover:bg-gray-100 p-2 rounded-full transition-colors duration-150"
                >
                  <X className="h-6 w-6" />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-6">
                <div className="bg-gray-50 rounded-xl p-6 border-2 border-gray-100">
                  <div className="whitespace-pre-wrap text-sm text-gray-700 leading-relaxed">
                    {selectedBody}
                  </div>
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-b-2xl">
                <button
                  onClick={closeBodyModal}
                  className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-150 font-medium"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 