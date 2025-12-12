// App.js - Enhanced Version

import React, { useEffect, useState } from "react";
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { GoogleOAuthProvider } from "@react-oauth/google";
import { initializeAuth, authAPI } from "./services/api";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import EmployeeList from "./components/EmployeeList";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import NotFound from "./components/NotFound.js";
import "./index.css";

// Initialize auth on app load
initializeAuth();

// Protected Route Component with Auth Check
const ProtectedRoute = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const location = useLocation();

  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem("access_token");
      
      if (!token) {
        setIsAuthenticated(false);
        return;
      }
      
      try {
        // Verify token is valid by fetching user data
        await authAPI.getCurrentUser();
        setIsAuthenticated(true);
      } catch (error) {
        console.error("Auth check failed:", error);
        setIsAuthenticated(false);
      }
    };
    
    checkAuth();
  }, [location]);

  if (isAuthenticated === null) {
    // Show loading state
    return (
      <div className="loading-container" style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '100vh'
      }}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" state={{ from: location }} />;
};

// Main Layout Component
const MainLayout = ({ children }) => {
  return (
    <div className="app-layout">
      <Navbar />
      <div className="main-content" style={{
        display: 'flex',
        minHeight: 'calc(100vh - 70px)'
      }}>
        <Sidebar />
        <main className="content-area" style={{
          flex: 1,
          padding: '24px',
          backgroundColor: 'var(--background-color)'
        }}>
          {children}
        </main>
      </div>
    </div>
  );
};

const App = () => {
  const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID ||
  "60209345033-dagb9pvr7maru9uq13i7ntoj4p513ls5.apps.googleusercontent.com";

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <Router>
        <div className="App">
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<Login />} />
            
            {/* Protected Routes with Main Layout */}
            <Route path="/" element={
              <ProtectedRoute>
                <MainLayout>
                  <Navigate to="/dashboard" />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <MainLayout>
                  <Dashboard />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            <Route path="/employees" element={
              <ProtectedRoute>
                <MainLayout>
                  <EmployeeList />
                </MainLayout>
              </ProtectedRoute>
            } />
            
            {/* Fallback route for SPA - Fixes 404 on refresh */}
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </Router>
    </GoogleOAuthProvider>
  );
};

export default App;