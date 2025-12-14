import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { GoogleOAuthProvider } from '@react-oauth/google';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import './App.css';

const App = () => {
  // Use the environment variable or fallback
  const googleClientId = process.env.REACT_APP_GOOGLE_CLIENT_ID || 
    "60209345033-dagb9pvr7maru9uq13i7ntoj4p513ls5.apps.googleusercontent.com";

  console.log('App initialized with:', {
    googleClientId: googleClientId ? 'Set ✓' : 'Not set ✗',
    apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8001',
    isDocker: process.env.NODE_ENV === 'production'
  });

  return (
    <GoogleOAuthProvider clientId={googleClientId}>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/" element={<Navigate to="/login" />} />
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        </div>
      </Router>
    </GoogleOAuthProvider>
  );
};

export default App;