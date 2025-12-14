import axios from 'axios';

// IMPORTANT: For Docker with network_mode: host, backend is at localhost:8001
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';

console.log('API Service initialized with URL:', API_URL);

// Generate a simple device ID
const getDeviceId = () => {
  let deviceId = localStorage.getItem('device_id');
  if (!deviceId) {
    deviceId = 'device_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('device_id', deviceId);
  }
  return deviceId;
};

// Get device type
const getDeviceType = () => {
  const ua = navigator.userAgent;
  if (/(tablet|ipad|playbook|silk)|(android(?!.*mobi))/i.test(ua)) {
    return 'tablet';
  }
  if (/Mobile|Android|iP(hone|od)|IEMobile|BlackBerry|Kindle|Silk-Accelerated|(hpw|web)OS|Opera M(obi|ini)/.test(ua)) {
    return 'mobile';
  }
  return 'desktop';
};

// Create axios instance with proper configuration for Docker
const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // Important for cookies to work properly
  withCredentials: true,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  async (error) => {
    console.error('API Error:', {
      url: error.config?.url,
      status: error.response?.status,
      message: error.message
    });
    
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        console.log('Attempting token refresh...');
        const refreshResponse = await axios.post(
          `${API_URL}/api/auth/refresh`,
          {},
          { 
            withCredentials: true,
            headers: {
              'Content-Type': 'application/json'
            }
          }
        );
        
        if (refreshResponse.data.access_token) {
          console.log('Token refreshed successfully');
          localStorage.setItem('access_token', refreshResponse.data.access_token);
          originalRequest.headers.Authorization = `Bearer ${refreshResponse.data.access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API functions
export const authAPI = {
  googleLogin: async (credential) => {
    const deviceId = getDeviceId();
    const deviceType = getDeviceType();
    
    console.log('Google login request with:', {
      deviceId,
      deviceType,
      apiUrl: API_URL
    });
    
    const response = await axios.post(
      `${API_URL}/api/auth/google-login`,
      { token: credential },
      {
        headers: {
          'X-Device-ID': deviceId,
          'X-Device-Type': deviceType,
          'Content-Type': 'application/json'
        },
        withCredentials: true
      }
    );
    return response;
  },

  refreshToken: async () => {
    console.log('Refreshing token...');
    const response = await axios.post(
      `${API_URL}/api/auth/refresh`,
      {},
      { 
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    return response;
  },

  logout: async () => {
    console.log('Logging out...');
    const response = await axios.post(
      `${API_URL}/api/auth/logout`,
      {},
      { 
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    return response;
  },

  getCurrentUser: async () => {
    const response = await api.get('/api/auth/me');
    return response;
  },

  // Test endpoint
  testProtectedEndpoint: async () => {
    const response = await api.get('/api/auth/me');
    return response;
  }
};

// Token management
export const setAccessToken = (token) => {
  localStorage.setItem('access_token', token);
  console.log('Access token saved to localStorage');
};

export const getAccessToken = () => {
  return localStorage.getItem('access_token');
};

export const clearAuthData = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('user');
  localStorage.removeItem('device_id');
  console.log('Auth data cleared');
};

// Initialize auth
export const initializeAuth = () => {
  const token = getAccessToken();
  if (token) {
    console.log('Auth initialized with existing token');
  } else {
    console.log('No existing auth token found');
  }
};

export default api;