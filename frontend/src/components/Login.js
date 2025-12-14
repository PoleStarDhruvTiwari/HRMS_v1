import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { GoogleLogin } from '@react-oauth/google';
import { authAPI, setAccessToken } from '../services/api';

const Login = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [debugInfo, setDebugInfo] = useState({});
  const navigate = useNavigate();

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');
      setDebugInfo({});

      console.log('=== LOGIN START ===');
      console.log('Google credential received:', credentialResponse.credential ? 'Yes' : 'No');
      
      if (!credentialResponse.credential) {
        throw new Error('No credential received from Google');
      }

      console.log('Making request to backend...');
      console.log('Backend URL:', process.env.REACT_APP_API_URL);
      
      const response = await authAPI.googleLogin(credentialResponse.credential);
      console.log('Backend response received:', {
        status: response.status,
        data: response.data,
        headers: response.headers
      });

      // Save access token
      const accessToken = response.data?.tokens?.access_token || response.data?.access_token;
      if (accessToken) {
        setAccessToken(accessToken);
        console.log('Access token saved:', accessToken.substring(0, 50) + '...');
      } else {
        console.warn('No access token in response');
      }

      // Save user data
      if (response.data?.user) {
        localStorage.setItem('user', JSON.stringify(response.data.user));
        console.log('User data saved:', response.data.user.email);
      }

      // Set debug info for display
      setDebugInfo({
        backendUrl: process.env.REACT_APP_API_URL,
        hasToken: !!accessToken,
        hasUser: !!response.data?.user,
        cookies: document.cookie ? 'Present' : 'None'
      });

      setSuccess('Login successful! Redirecting to dashboard...');
      
      // Redirect to dashboard after a short delay
      setTimeout(() => {
        navigate('/dashboard');
      }, 1500);

    } catch (err) {
      console.error('=== LOGIN ERROR ===', err);
      
      let errorMessage = 'Login failed. Please try again.';
      let debugDetails = {};
      
      if (err.response) {
        // Server responded with error
        errorMessage = err.response.data?.detail || 
                       err.response.data?.message || 
                       `Server error: ${err.response.status}`;
        debugDetails = {
          status: err.response.status,
          data: err.response.data,
          headers: err.response.headers
        };
        console.log('Server response:', err.response.data);
      } else if (err.request) {
        // No response received
        errorMessage = 'No response from server. Check if backend is running.';
        debugDetails = { request: 'No response received' };
        console.log('No response received');
      } else {
        // Other errors
        errorMessage = err.message || errorMessage;
        debugDetails = { error: err.message };
      }
      
      setError(errorMessage);
      setDebugInfo(debugDetails);
      
    } finally {
      setLoading(false);
      console.log('=== LOGIN END ===');
    }
  };

  const handleGoogleError = () => {
    setError('Google login failed. Please try again.');
    setDebugInfo({ googleError: 'Google OAuth error' });
  };

  return (
    <div className="container" style={{ 
      maxWidth: '500px', 
      margin: '50px auto',
      padding: '40px 20px'
    }}>
      <div className="card">
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h1 style={{ marginBottom: '10px', color: '#333' }}>Google Auth Test</h1>
          <p style={{ color: '#666' }}>Test Google authentication and token generation</p>
        </div>

        {error && (
          <div className="alert alert-error">
            <strong>Error:</strong> {error}
          </div>
        )}

        {success && (
          <div className="alert alert-success">
            {success}
          </div>
        )}

        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <div style={{ marginBottom: '20px' }}>
            <GoogleLogin
              onSuccess={handleGoogleSuccess}
              onError={handleGoogleError}
              theme="filled_blue"
              size="large"
              shape="rectangular"
              width="300"
              text="signin_with"
              logo_alignment="center"
            />
          </div>

          {loading && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
              <div className="spinner"></div>
              <span>Authenticating...</span>
            </div>
          )}
        </div>

        {/* Debug Information */}
        {Object.keys(debugInfo).length > 0 && (
          <div className="card" style={{ marginTop: '20px', background: '#f8f9fa' }}>
            <h4 style={{ marginBottom: '10px', color: '#666' }}>Debug Info:</h4>
            <pre style={{ 
              fontSize: '12px', 
              color: '#666',
              background: '#fff',
              padding: '10px',
              borderRadius: '4px',
              overflow: 'auto',
              maxHeight: '200px'
            }}>
              {JSON.stringify(debugInfo, null, 2)}
            </pre>
          </div>
        )}

        <div className="alert alert-info">
          <strong>Configuration:</strong>
          <ul style={{ marginTop: '10px', paddingLeft: '20px' }}>
            <li>Backend URL: {process.env.REACT_APP_API_URL || 'Not set'}</li>
            <li>Google Client ID: {process.env.REACT_APP_GOOGLE_CLIENT_ID ? 'Set ✓' : 'Not set ✗'}</li>
            <li>Cookies: {document.cookie ? 'Present' : 'None'}</li>
          </ul>
        </div>

        <div style={{ 
          marginTop: '30px', 
          paddingTop: '20px', 
          borderTop: '1px solid #e2e8f0',
          textAlign: 'center',
          color: '#666',
          fontSize: '14px'
        }}>
          <p><strong>Docker Setup:</strong> network_mode: host enabled</p>
          <p>Backend should be accessible at: http://localhost:8001</p>
        </div>
      </div>
    </div>
  );
};

export default Login;