// frontend/src/components/NotFound.js
import React from 'react';
import { Link } from 'react-router-dom';

const NotFound = () => {
  return (
    <div className="card" style={{
      textAlign: 'center',
      padding: '60px 20px',
      maxWidth: '600px',
      margin: '100px auto'
    }}>
      <h1 style={{ fontSize: '48px', color: '#ef4444', marginBottom: '20px' }}>404</h1>
      <h2 style={{ marginBottom: '20px' }}>Page Not Found</h2>
      <p style={{ marginBottom: '30px', color: '#64748b' }}>
        The page you are looking for doesn't exist or has been moved.
      </p>
      <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
        <Link to="/" className="btn btn-primary">
          Go to Dashboard
        </Link>
        <Link to="/login" className="btn btn-outline">
          Login Page
        </Link>
      </div>
    </div>
  );
};

export default NotFound;