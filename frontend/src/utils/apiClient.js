/**
 * Enhanced API client for OSINT Investigation Platform
 * Handles all backend communication with proper error handling and response formatting
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

class APIClient {
  constructor(baseURL = API_BASE_URL) {
    this.baseURL = baseURL;
    this.timeout = 30000; // 30 seconds default
  }

  /**
   * Make a request to the backend
   */
  async request(endpoint, options = {}) {
    const {
      method = 'GET',
      body = null,
      headers = {},
      timeout = this.timeout,
    } = options;

    const url = `${this.baseURL}${endpoint}`;
    const config = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };

    if (body) {
      config.body = JSON.stringify(body);
    }

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeout);

      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          await response.text()
        );
      }

      const data = await response.json();
      return data;
    } catch (error) {
      if (error instanceof APIError) throw error;
      throw new APIError(
        error.message || 'Network request failed',
        0,
        error
      );
    }
  }

  // Investigation endpoints
  async createInvestigation(username, email, phone) {
    return this.request('/api/investigation/create', {
      method: 'POST',
      body: {
        username,
        ...(email && { email }),
        ...(phone && { phone }),
      },
    });
  }

  async getInvestigation(caseId) {
    return this.request(`/api/investigation/${caseId}`);
  }

  async getInvestigationResult(caseId) {
    return this.request(`/api/investigation/${caseId}/result`);
  }

  async startLightScan(caseId) {
    return this.request(`/api/investigation/scan/${caseId}/light`, {
      method: 'POST',
    });
  }

  async startDeepScan(caseId) {
    return this.request(`/api/investigation/scan/${caseId}/deep`, {
      method: 'POST',
    });
  }

  async listInvestigations(page = 1, limit = 10) {
    return this.request(`/api/investigation/list?page=${page}&limit=${limit}`);
  }

  // Phone endpoints
  async phoneUniqueLookup(phone) {
    return this.request('/api/phone/lookup', {
      method: 'POST',
      body: { phone },
    });
  }

  async phoneBatchLookup(phones) {
    return this.request('/api/phone/batch-lookup', {
      method: 'POST',
      body: { phone_numbers: phones },
    });
  }

  async validatePhone(phone) {
    return this.request(`/api/phone/validate/${encodeURIComponent(phone)}`);
  }

  // Graph endpoints
  async getGraph(caseId) {
    return this.request(`/api/graph/${caseId}`);
  }

  async getGraphStatistics(caseId) {
    return this.request(`/api/graph/${caseId}/statistics`);
  }

  async getGraphConnectedNodes(caseId, nodeId, depth = 1) {
    return this.request(
      `/api/graph/${caseId}/connected/${encodeURIComponent(nodeId)}?depth=${depth}`
    );
  }

  async getNodeDetails(caseId, nodeId) {
    return this.request(`/api/graph/${caseId}/node/${encodeURIComponent(nodeId)}`);
  }

  async exportGraph(caseId, format = 'json') {
    return this.request(`/api/graph/${caseId}/export/${format}`);
  }

  // Report endpoints
  async generateReport(caseId, format = 'pdf') {
    return this.request(`/api/report/${caseId}/generate`, {
      method: 'POST',
      body: { format },
    });
  }

  async getReport(caseId, format = 'json') {
    return this.request(`/api/report/${caseId}/${format}`);
  }
}

class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.name = 'APIError';
    this.status = status;
    this.details = details;
  }
}

// Export singleton instance
export const api = new APIClient();
export { APIError, APIClient };
