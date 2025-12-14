import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, getAccessToken, clearAuthData } from '../services/api';

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState('');
  const [testResult, setTestResult] = useState('');
  const [deviceInfo, setDeviceInfo] = useState({});
  const [networkInfo, setNetworkInfo] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    loadUserData();
    loadDeviceInfo();
    checkNetwork();
  }, []);

  const loadUserData = async () => {
    try {
      setLoading(true);
      const response = await authAPI.getCurrentUser();
      setUser(response.data);
      
      // Get token from localStorage
      const storedToken = getAccessToken();
      setToken(storedToken || 'No token found');
      
    } catch (error) {
      console.error('Failed to load user:', error);
      if (error.response?.status === 401) {
        // Token expired or invalid
        clearAuthData();
        navigate('/login');
      }
    } finally {
      setLoading(false);
    }
  };

  const loadDeviceInfo = () => {
    const deviceId = localStorage.getItem('device_id');
    const deviceType = navigator.userAgent.match(/Mobile/) ? 'Mobile' : 'Desktop';
    
    setDeviceInfo({
      deviceId: deviceId || 'Not set',
      deviceType: deviceType,
      userAgent: navigator.userAgent.substring(0, 50) + '...'
    });
  };

  const checkNetwork = async () => {
    try {
      // Try to fetch backend health or info
      const backendUrl = process.env.REACT_APP_API_URL || 'http://localhost:8001';
      const response = await fetch(`${backendUrl}/api/auth/me`, {
        method: 'GET',
        headers: {
          'Accept': 'application/json'
        }
      }).catch(() => null);
      
      setNetworkInfo({
        backendUrl: backendUrl,
        accessible: response ? 'Yes ✓' : 'No ✗',
        status: response?.status || 'No response'
      });
    } catch (error) {
      setNetworkInfo({
        backendUrl: process.env.REACT_APP_API_URL,
        accessible: 'No ✗',
        error: error.message
      });
    }
  };

  const handleLogout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      clearAuthData();
      navigate('/login');
    }
  };

  const handleTestProtectedEndpoint = async () => {
    try {
      setTestResult('Testing protected endpoint...');
      const response = await authAPI.testProtectedEndpoint();
      setTestResult(`✅ Success! User: ${response.data.email}`);
    } catch (error) {
      setTestResult(`❌ Failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleRefreshToken = async () => {
    try {
      setTestResult('Refreshing token...');
      const response = await authAPI.refreshToken();
      if (response.data.access_token) {
        localStorage.setItem('access_token', response.data.access_token);
        setToken(response.data.access_token);
        setTestResult('✅ Token refreshed successfully!');
      }
    } catch (error) {
      setTestResult(`❌ Refresh failed: ${error.response?.data?.detail || error.message}`);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '100px 20px' }}>
        <div className="spinner" style={{ width: '40px', height: '40px', margin: '0 auto 20px' }}></div>
        <p>Loading user data...</p>
      </div>
    );
  }

  return (
    <div className="container">
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        marginBottom: '30px'
      }}>
        <h1>Dashboard</h1>
        <button className="button" onClick={handleLogout}>
          Logout
        </button>
      </div>

      {/* Network Info Card */}
      <div className="card" style={{ background: networkInfo.accessible.includes('✓') ? '#d1fae5' : '#fee2e2' }}>
        <h2 style={{ marginBottom: '20px' }}>Docker Network Status</h2>
        <div style={{ lineHeight: '1.8' }}>
          <p><strong>Backend URL:</strong> {networkInfo.backendUrl}</p>
          <p><strong>Accessible:</strong> {networkInfo.accessible}</p>
          <p><strong>Status:</strong> {networkInfo.status}</p>
          {networkInfo.error && <p><strong>Error:</strong> {networkInfo.error}</p>}
          <p><strong>Mode:</strong> Docker with network_mode: host</p>
        </div>
      </div>

      {/* User Info Card */}
      <div className="card">
        <h2 style={{ marginBottom: '20px' }}>User Information</h2>
        {user ? (
          <div style={{ lineHeight: '1.8' }}>
            <p><strong>Email:</strong> {user.email}</p>
            <p><strong>Name:</strong> {user.name || 'Not provided'}</p>
            <p><strong>Admin:</strong> {user.is_admin ? 'Yes' : 'No'}</p>
            <p><strong>Last Login:</strong> {user.last_login ? new Date(user.last_login).toLocaleString() : 'Never'}</p>
          </div>
        ) : (
          <p>No user data found</p>
        )}
      </div>

      {/* Token Card */}
      <div className="card">
        <h2 style={{ marginBottom: '20px' }}>Bearer Token</h2>
        <div className="token-display" style={{ marginBottom: '20px', fontSize: '12px' }}>
          {token ? token.substring(0, 100) + '...' : 'No token'}
        </div>
        <div>
          <button 
            className="button" 
            onClick={() => copyToClipboard(token)}
            style={{ marginRight: '10px' }}
          >
            Copy Token
          </button>
          <button 
            className="button" 
            onClick={handleRefreshToken}
            style={{ background: '#10b981', marginRight: '10px' }}
          >
            Refresh Token
          </button>
          <button 
            className="button" 
            onClick={() => {
              console.log('Full token:', token);
              alert('Check console for full token');
            }}
            style={{ background: '#8b5cf6' }}
          >
            View Full Token
          </button>
        </div>
      </div>

      {/* API Tests Card */}
      <div className="card">
        <h2 style={{ marginBottom: '20px' }}>API Tests</h2>
        
        <div style={{ marginBottom: '20px' }}>
          <button 
            className="button" 
            onClick={handleTestProtectedEndpoint}
            style={{ marginRight: '10px' }}
          >
            Test Protected Endpoint
          </button>
          
          <button 
            className="button" 
            onClick={() => {
              setTestResult('');
              loadUserData();
            }}
            style={{ background: '#6366f1', marginRight: '10px' }}
          >
            Reload User Data
          </button>

          <button 
            className="button" 
            onClick={checkNetwork}
            style={{ background: '#f59e0b' }}
          >
            Check Network
          </button>
        </div>

        {testResult && (
          <div className={testResult.includes('✅') ? 'alert alert-success' : 'alert alert-error'}>
            {testResult}
          </div>
        )}
      </div>

      {/* Debug Info Card */}
      <div className="card">
        <h2 style={{ marginBottom: '20px' }}>Debug Information</h2>
        <div style={{ lineHeight: '1.8', fontSize: '14px', color: '#666' }}>
          <p><strong>Environment:</strong> {process.env.NODE_ENV}</p>
          <p><strong>Google Client ID:</strong> {process.env.REACT_APP_GOOGLE_CLIENT_ID ? 'Set ✓' : 'Not set ✗'}</p>
          <p><strong>Local Storage:</strong> {Object.keys(localStorage).join(', ')}</p>
          <p><strong>Cookies:</strong> {document.cookie || 'None'}</p>
          <p><strong>Device ID:</strong> {deviceInfo.deviceId}</p>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;