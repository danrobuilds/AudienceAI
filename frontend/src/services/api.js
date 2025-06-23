import axios from 'axios';

// Base API configuration - using empty string to leverage the proxy in package.json
const API_BASE_URL = process.env.REACT_APP_API_URL || '';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes timeout for long-running operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to: ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// User Queries API
export const userQueriesAPI = {
  generateContent: async (prompt) => {
    try {
      const response = await apiClient.post('/queries/generate', {
        prompt: prompt
      });
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to generate content');
    }
  },

  generateContentStream: async (prompt, onMessage) => {
    try {
      const response = await fetch(`${API_BASE_URL}/queries/generate-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: prompt })
      });

      if (!response.ok) {
        throw new Error('Failed to start streaming');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onMessage(data);
            } catch (e) {
              console.warn('Failed to parse SSE data:', line);
            }
          }
        }
      }
    } catch (error) {
      throw new Error('Streaming failed: ' + error.message);
    }
  },

  getStatus: async () => {
    try {
      const response = await apiClient.get('/queries/status');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get status');
    }
  }
};

// Uploads API
export const uploadsAPI = {
  uploadMultiple: async (files, onProgress) => {
    try {
      const formData = new FormData();
      files.forEach((file) => {
        formData.append('files', file);
      });

      const response = await apiClient.post('/documents/upload-multiple', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            onProgress(progress);
          }
        }
      });

      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to upload files');
    }
  },

  listDocuments: async () => {
    try {
      const response = await apiClient.get('/documents/list');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to list documents');
    }
  },

  deleteDocument: async (documentId) => {
    try {
      const response = await apiClient.delete(`/documents/delete/${documentId}`);
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to delete document');
    }
  },

  getHealth: async () => {
    try {
      const response = await apiClient.get('/documents/health');
      return response.data;
    } catch (error) {
      throw new Error(error.response?.data?.detail || 'Failed to get upload service health');
    }
  }
};

export default apiClient; 