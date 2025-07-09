import { RequestLogStats, RequestLog } from '../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private async fetchWithErrorHandling<T>(url: string): Promise<T> {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async getRequestStats(startDate?: string, endDate?: string): Promise<RequestLogStats> {
    let url = `${API_BASE_URL}/request-logs/stats`;
    const params = new URLSearchParams();
    
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }

    return this.fetchWithErrorHandling<RequestLogStats>(url);
  }

  async getUserRequestLogs(userId: string, limit: number = 100): Promise<RequestLog[]> {
    const url = `${API_BASE_URL}/request-logs/user/${userId}?limit=${limit}`;
    return this.fetchWithErrorHandling<RequestLog[]>(url);
  }

  async getRequestLog(logId: string): Promise<RequestLog> {
    const url = `${API_BASE_URL}/request-logs/${logId}`;
    return this.fetchWithErrorHandling<RequestLog>(url);
  }
}

export const apiService = new ApiService(); 