// services/api.js - Enhanced Version

import axios from "axios";

const API_URL = process.env.REACT_APP_API_URL || "http://localhost:8001";


// Global token storage
let accessToken = localStorage.getItem("access_token");
let refreshPromise = null; // To prevent multiple refresh calls

// Create axios instance
const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Essential for httpOnly cookies
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor with enhanced refresh logic
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Only handle 401 errors (unauthorized)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // If we're already refreshing, wait for that promise
      if (refreshPromise) {
        return refreshPromise.then(() => {
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
          return api(originalRequest);
        });
      }
      
      // Create refresh promise
      refreshPromise = (async () => {
        try {
          console.log("Attempting to refresh access token...");
          
          // Call refresh endpoint - refresh token should be in httpOnly cookie
          const refreshResponse = await api.post("/api/auth/refresh", {}, {
            skipAuthRefresh: true // Custom flag to prevent infinite loop
          });
          
          const newAccessToken = refreshResponse.data.tokens?.access_token || 
                                refreshResponse.data.access_token;
          
          if (!newAccessToken) {
            throw new Error("No access token in refresh response");
          }
          
          // Update tokens
          accessToken = newAccessToken;
          localStorage.setItem("access_token", newAccessToken);
          
          console.log("Token refreshed successfully");
          return newAccessToken;
        } catch (refreshError) {
          console.error("Token refresh failed:", refreshError);
          
          // Clear everything and redirect to login
          accessToken = null;
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          
          // Only redirect if not already on login page
          if (!window.location.pathname.includes('/login')) {
            window.location.href = "/login";
          }
          
          throw refreshError;
        } finally {
          refreshPromise = null;
        }
      })();
      
      try {
        await refreshPromise;
        // Update the original request with new token
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        // Retry the original request
        return api(originalRequest);
      } catch (refreshError) {
        return Promise.reject(refreshError);
      }
    }
    
    // Handle other errors
    return Promise.reject(error);
  }
);

// Auth API methods
export const authAPI = {
  googleLogin: (token) => api.post("/api/auth/google-login", { token }),
  
  getCurrentUser: async () => {
    try {
      const response = await api.get("/api/auth/me");
      // Store user data
      if (response.data) {
        localStorage.setItem("user", JSON.stringify(response.data));
      }
      return response;
    } catch (error) {
      // Clear storage if unauthorized
      if (error.response?.status === 401) {
        localStorage.removeItem("access_token");
        localStorage.removeItem("user");
      }
      throw error;
    }
  },
  
  logout: async () => {
    try {
      const response = await api.post("/api/auth/logout");
      return response;
    } finally {
      // Always clear local storage on logout
      accessToken = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("user");
    }
  },
  
  // Check if user is authenticated
  isAuthenticated: () => {
    return !!accessToken;
  }
};

// Employee API methods
export const employeeAPI = {
  getEmployees: (params) => api.get("/api/employees", { params }),
  getEmployee: (id) => api.get(`/api/employees/${id}`),
  createEmployee: (data) => api.post("/api/employees", data),
  updateEmployee: (id, data) => api.put(`/api/employees/${id}`, data),
  deleteEmployee: (id) => api.delete(`/api/employees/${id}`),
};

// Token management functions
export const setAccessToken = (token) => {
  accessToken = token;
  localStorage.setItem("access_token", token);
};

export const getAccessToken = () => accessToken;

export const clearTokens = () => {
  accessToken = null;
  localStorage.removeItem("access_token");
  localStorage.removeItem("user");
};

// Initialize token from storage on app load
export const initializeAuth = () => {
  const token = localStorage.getItem("access_token");
  if (token) {
    accessToken = token;
  }
};

export default api;