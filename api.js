/**
 * JARVIS Centralized API Client Service
 * 
 * Provides a unified, robust interface for the frontend to communicate with
 * the FastAPI backend. Handles base URL resolution, network error handling,
 * health monitoring, task planning, and execution polling.
 */

(function (global) {
  'use strict';

  // Configurable base URL:
  // 1. window.JARVIS_CONFIG?.API_BASE_URL
  // 2. localStorage 'jarvis_api_base_url'
  // 3. Current origin (if hosted on :8000)
  // 4. Fallback to default http://127.0.0.1:8000
  function resolveDefaultBaseUrl() {
    if (global.JARVIS_CONFIG && global.JARVIS_CONFIG.API_BASE_URL) {
      return global.JARVIS_CONFIG.API_BASE_URL.replace(/\/+$/, '');
    }
    try {
      const stored = localStorage.getItem('jarvis_api_base_url');
      if (stored) return stored.replace(/\/+$/, '');
    } catch (_) {
      // Storage unavailable or disabled
    }
    if (typeof window !== 'undefined' && window.location) {
      const origin = window.location.origin;
      if (origin && origin.includes(':8000')) {
        return origin;
      }
    }
    return 'http://127.0.0.1:8000';
  }

  let baseUrl = resolveDefaultBaseUrl();

  class JarvisApiError extends Error {
    constructor(message, status = null, details = null) {
      super(message);
      this.name = 'JarvisApiError';
      this.status = status;
      this.details = details;
    }
  }

  async function request(endpoint, options = {}) {
    const url = `${baseUrl}${endpoint}`;
    const defaultHeaders = {
      'Accept': 'application/json',
    };

    if (options.body && typeof options.body === 'string') {
      defaultHeaders['Content-Type'] = 'application/json';
    }

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...(options.headers || {}),
      },
    };

    try {
      const response = await fetch(url, config);
      let data = null;
      const contentType = response.headers.get('content-type') || '';
      
      if (contentType.includes('application/json')) {
        data = await response.json();
      } else {
        const text = await response.text();
        try {
          data = JSON.parse(text);
        } catch (_) {
          data = text;
        }
      }

      if (!response.ok) {
        let errorMsg = `HTTP ${response.status}: Request failed`;
        if (data && typeof data === 'object') {
          if (data.detail) {
            errorMsg = Array.isArray(data.detail)
              ? data.detail.map(d => d.msg || JSON.stringify(d)).join('; ')
              : String(data.detail);
          } else if (data.message) {
            errorMsg = String(data.message);
          } else if (data.error) {
            errorMsg = String(data.error);
          }
        }
        throw new JarvisApiError(errorMsg, response.status, data);
      }

      return data;
    } catch (err) {
      if (err instanceof JarvisApiError) {
        throw err;
      }
      // Network failure or CORS block
      throw new JarvisApiError(
        `Unable to connect to JARVIS Core at ${baseUrl}. Ensure the backend is active (python -m uvicorn backend.main:app --reload).`,
        0,
        { originalError: err.message }
      );
    }
  }

  const JarvisApi = {
    getBaseUrl() {
      return baseUrl;
    },

    setBaseUrl(newUrl) {
      if (!newUrl) return;
      baseUrl = newUrl.replace(/\/+$/, '');
      try {
        localStorage.setItem('jarvis_api_base_url', baseUrl);
      } catch (_) {}
    },

    /**
     * Check backend health status: GET /health
     */
    async healthCheck() {
      return await request('/health', { method: 'GET' });
    },

    /**
     * Root endpoint: GET /
     */
    async getRoot() {
      return await request('/', { method: 'GET' });
    },

    /**
     * Retrieve all tracked tasks: GET /api/tasks
     */
    async listTasks() {
      return await request('/api/tasks', { method: 'GET' });
    },

    /**
     * Submit a task instruction to generate an AI plan: POST /api/tasks
     * @param {string} instruction
     */
    async createTask(instruction) {
      if (!instruction || typeof instruction !== 'string' || instruction.trim().length < 5) {
        throw new JarvisApiError('Instruction must be at least 5 characters long.', 400);
      }
      return await request('/api/tasks', {
        method: 'POST',
        body: JSON.stringify({ instruction: instruction.trim() }),
      });
    },

    /**
     * Retrieve details and status of a task: GET /api/tasks/{task_id}
     * @param {string} taskId
     */
    async getTask(taskId) {
      if (!taskId) throw new JarvisApiError('Task ID is required.', 400);
      return await request(`/api/tasks/${encodeURIComponent(taskId)}`, {
        method: 'GET',
      });
    },

    /**
     * Start execution of a planned task: POST /api/tasks/{task_id}/execute
     * @param {string} taskId
     */
    async executeTask(taskId) {
      if (!taskId) throw new JarvisApiError('Task ID is required.', 400);
      return await request(`/api/tasks/${encodeURIComponent(taskId)}/execute`, {
        method: 'POST',
      });
    },

    /**
     * Continuously poll a task until it reaches a terminal or desired state.
     * @param {string} taskId
     * @param {Function} onUpdate Callback invoked with fresh task data
     * @param {Object} options { intervalMs = 1200, maxAttempts = 120, stopStatuses = [] }
     */
    async pollTask(taskId, onUpdate = null, options = {}) {
      const intervalMs = options.intervalMs || 1200;
      const maxAttempts = options.maxAttempts || 150;
      const stopStatuses = new Set(
        options.stopStatuses || ['planned', 'completed', 'blocked', 'failed']
      );

      let attempts = 0;
      while (attempts < maxAttempts) {
        const task = await this.getTask(taskId);
        if (typeof onUpdate === 'function') {
          onUpdate(task);
        }

        if (stopStatuses.has(task.status)) {
          return task;
        }

        await new Promise((resolve) => setTimeout(resolve, intervalMs));
        attempts++;
      }

      throw new JarvisApiError(
        'Task polling timed out before reaching completion.',
        408
      );
    },

    /**
     * Run the local meeting notes briefing workflow
     */
    async runBriefingWorkflow() {
      return await request('/api/workflows/briefing', {
        method: 'POST',
      });
    },

    /**
     * Retrieve real-time memory telemetry and audit insights: GET /api/memory/insights
     */
    async getMemoryInsights() {
      return await request('/api/memory/insights', { method: 'GET' });
    },

    /**
     * Retrieve persistent memories: GET /api/memory/items
     */
    async listMemories() {
      return await request('/api/memory/items', { method: 'GET' });
    },

    /**
     * Ingest and persist a new memory record: POST /api/memory/items
     */
    async storeMemory(text, cat = 'GENERAL', tag = 'OPERATOR') {
      return await request('/api/memory/items', {
        method: 'POST',
        body: JSON.stringify({ text, cat, tag }),
      });
    },

    /**
     * Delete a memory record: DELETE /api/memory/items/{id}
     */
    async deleteMemory(memoryId) {
      return await request(`/api/memory/items/${encodeURIComponent(memoryId)}`, {
        method: 'DELETE',
      });
    },
  };


  global.JarvisApi = JarvisApi;
  global.JarvisApiError = JarvisApiError;
})(typeof window !== 'undefined' ? window : globalThis);
