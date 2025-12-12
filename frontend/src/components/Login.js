// components/Login.js - Enhanced Version

import React, { useState, useEffect } from "react";
import { GoogleLogin } from "@react-oauth/google";
import { useNavigate, useLocation } from "react-router-dom";
import { authAPI, setAccessToken } from "../services/api";
import { FcGoogle } from "react-icons/fc";
import { FaBuilding, FaUsers, FaChartLine } from "react-icons/fa";

const Login = () => {
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || "/dashboard";

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (token) {
      navigate(from, { replace: true });
    }
  }, [navigate, from]);

  const handleGoogleSuccess = async (credentialResponse) => {
    try {
      setError("");
      setLoading(true);
      
      const response = await authAPI.googleLogin(credentialResponse.credential);
      
      // Save access token
      if (response.data.tokens?.access_token) {
        setAccessToken(response.data.tokens.access_token);
      } else if (response.data.access_token) {
        setAccessToken(response.data.access_token);
      }
      
      // Save user data
      if (response.data.user) {
        localStorage.setItem("user", JSON.stringify(response.data.user));
      }
      
      // Redirect to intended page or dashboard
      navigate(from, { replace: true });
    } catch (err) {
      console.error("Login error:", err);
      setError(err.response?.data?.message || "Login failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleError = () => {
    setError("Google login failed. Please try again.");
  };

  return (
    <div className="login-container" style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <div style={{
        display: 'flex',
        maxWidth: '1000px',
        width: '100%',
        background: 'white',
        borderRadius: '20px',
        overflow: 'hidden',
        boxShadow: '0 20px 60px rgba(0,0,0,0.3)'
      }}>
        {/* Left Side - Branding & Features */}
        <div style={{
          flex: 1,
          background: 'linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%)',
          color: 'white',
          padding: '60px 40px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <div style={{ marginBottom: '40px' }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              marginBottom: '20px'
            }}>
              <FaBuilding size={32} />
              <h1 style={{ fontSize: '28px', fontWeight: '700' }}>HRMS Pro</h1>
            </div>
            <p style={{
              fontSize: '16px',
              opacity: '0.9',
              lineHeight: '1.6'
            }}>
              Enterprise-grade Human Resource Management System
            </p>
          </div>
          
          <div style={{ marginTop: '40px' }}>
            <h3 style={{ marginBottom: '20px', fontSize: '18px' }}>Key Features</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              {[
                { icon: <FaUsers />, text: 'Comprehensive Employee Management' },
                { icon: <FaChartLine />, text: 'Real-time Analytics & Reporting' },
                { icon: <FaBuilding />, text: 'Department & Role Management' }
              ].map((feature, index) => (
                <div key={index} style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px'
                }}>
                  <div style={{
                    background: 'rgba(255,255,255,0.2)',
                    borderRadius: '50%',
                    padding: '8px'
                  }}>
                    {feature.icon}
                  </div>
                  <span>{feature.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
        
        {/* Right Side - Login Form */}
        <div style={{
          flex: 1,
          padding: '60px 40px',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center'
        }}>
          <div style={{ textAlign: 'center', marginBottom: '40px' }}>
            <h2 style={{
              fontSize: '28px',
              fontWeight: '700',
              color: '#1e293b',
              marginBottom: '8px'
            }}>
              Welcome Back
            </h2>
            <p style={{
              color: '#64748b',
              fontSize: '16px'
            }}>
              Sign in to access your HRMS dashboard
            </p>
          </div>
          
          {error && (
            <div style={{
              background: '#fee2e2',
              color: '#dc2626',
              padding: '12px 16px',
              borderRadius: '8px',
              marginBottom: '20px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>⚠</span>
              <span>{error}</span>
            </div>
          )}
          
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '20px'
          }}>
            <div style={{ width: '100%', maxWidth: '320px' }}>
              <GoogleLogin
                onSuccess={handleGoogleSuccess}
                onError={handleGoogleError}
                theme="filled_blue"
                size="large"
                shape="rectangular"
                width="100%"
                text="signin_with"
                logo_alignment="center"
              />
            </div>
            
            {loading && (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                color: '#64748b'
              }}>
                <div className="loading-spinner"></div>
                <span>Authenticating...</span>
              </div>
            )}
            
            <div style={{
              textAlign: 'center',
              marginTop: '30px',
              paddingTop: '30px',
              borderTop: '1px solid #e2e8f0',
              width: '100%'
            }}>
              <p style={{
                color: '#64748b',
                fontSize: '14px',
                lineHeight: '1.5'
              }}>
                <strong>Note:</strong> Use your company Google account to sign in.
                First-time users will be automatically registered.
              </p>
            </div>
          </div>
          
          <div style={{
            marginTop: '40px',
            textAlign: 'center',
            color: '#64748b',
            fontSize: '14px'
          }}>
            <p>Need help? Contact your system administrator</p>
            <p style={{ marginTop: '8px', opacity: '0.7' }}>
              HRMS Pro v1.0 • Secure Enterprise Platform
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;