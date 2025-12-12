// components/Dashboard.js - Enhanced Version

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { authAPI } from "../services/api";
import { 
  FaUsers, 
  FaCalendarCheck, 
  FaChartLine, 
  FaBuilding,
  FaBell,
  FaCog
} from "react-icons/fa";

const Dashboard = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalEmployees: 0,
    activeEmployees: 0,
    departments: 0,
    todayAttendance: 0
  });
  const navigate = useNavigate();

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        setLoading(true);
        const [userResponse] = await Promise.all([
          authAPI.getCurrentUser(),
          // Add more API calls for stats here
        ]);
        
        setUser(userResponse.data);
        
        // Mock stats - replace with actual API calls
        setStats({
          totalEmployees: 156,
          activeEmployees: 142,
          departments: 8,
          todayAttendance: 138
        });
        
      } catch (err) {
        console.error("Failed to load dashboard data", err);
        if (err.response?.status === 401) {
          navigate("/login");
        }
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, [navigate]);

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '400px'
      }}>
        <div className="loading-spinner"></div>
      </div>
    );
  }

  const statCards = [
    {
      title: "Total Employees",
      value: stats.totalEmployees,
      icon: <FaUsers />,
      color: "#3b82f6",
      change: "+12%"
    },
    {
      title: "Active Today",
      value: stats.todayAttendance,
      icon: <FaCalendarCheck />,
      color: "#10b981",
      change: "+5%"
    },
    {
      title: "Departments",
      value: stats.departments,
      icon: <FaBuilding />,
      color: "#8b5cf6",
      change: "+2"
    },
    {
      title: "Growth Rate",
      value: "24.5%",
      icon: <FaChartLine />,
      color: "#f59e0b",
      change: "+3.2%"
    }
  ];

  return (
    <div>
      {/* Header */}
      <div className="flex-between mb-6">
        <div>
          <h1 style={{
            fontSize: '28px',
            fontWeight: '700',
            color: 'var(--text-primary)'
          }}>
            Dashboard
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
            Welcome back, {user?.name}. Here's what's happening today.
          </p>
        </div>
        <div className="flex gap-4">
          <button className="btn btn-outline" style={{ padding: '8px 16px' }}>
            <FaBell />
            Notifications
          </button>
          <button className="btn btn-outline" style={{ padding: '8px 16px' }}>
            <FaCog />
            Settings
          </button>
        </div>
      </div>

      {/* Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '20px',
        marginBottom: '30px'
      }}>
        {statCards.map((stat, index) => (
          <div key={index} className="card" style={{ padding: '20px' }}>
            <div className="flex-between">
              <div>
                <p style={{
                  fontSize: '14px',
                  color: 'var(--text-secondary)',
                  marginBottom: '8px'
                }}>
                  {stat.title}
                </p>
                <p style={{
                  fontSize: '32px',
                  fontWeight: '700',
                  color: 'var(--text-primary)'
                }}>
                  {stat.value}
                </p>
              </div>
              <div style={{
                width: '48px',
                height: '48px',
                borderRadius: '12px',
                background: `${stat.color}20`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: stat.color
              }}>
                {stat.icon}
              </div>
            </div>
            <div style={{
              marginTop: '12px',
              fontSize: '14px',
              color: stat.change.startsWith('+') ? '#10b981' : '#ef4444'
            }}>
              {stat.change} from last month
            </div>
          </div>
        ))}
      </div>

      {/* Main Content */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '20px'
      }}>
        {/* Left Column */}
        <div>
          <div className="card">
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              marginBottom: '20px'
            }}>
              Recent Activity
            </h3>
            {/* Activity list would go here */}
            <div style={{ textAlign: 'center', padding: '40px', color: '#64748b' }}>
              Activity feed will appear here
            </div>
          </div>
        </div>

        {/* Right Column */}
        <div>
          <div className="card">
            <h3 style={{
              fontSize: '18px',
              fontWeight: '600',
              marginBottom: '20px'
            }}>
              Quick Actions
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <button 
                className="btn btn-primary"
                onClick={() => navigate("/employees")}
              >
                View All Employees
              </button>
              <button className="btn btn-outline">
                Generate Reports
              </button>
              <button className="btn btn-outline">
                Manage Departments
              </button>
            </div>
          </div>

          {/* User Info Card */}
          {user && (
            <div className="card" style={{ marginTop: '20px' }}>
              <h4 style={{
                fontSize: '16px',
                fontWeight: '600',
                marginBottom: '16px'
              }}>
                Your Profile
              </h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                {user.picture ? (
                  <img 
                    src={user.picture} 
                    alt={user.name}
                    style={{
                      width: '60px',
                      height: '60px',
                      borderRadius: '50%',
                      objectFit: 'cover'
                    }}
                  />
                ) : (
                  <div style={{
                    width: '60px',
                    height: '60px',
                    borderRadius: '50%',
                    background: '#e2e8f0',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#64748b'
                  }}>
                    <FaUsers size={24} />
                  </div>
                )}
                <div>
                  <div style={{ fontWeight: '600' }}>{user.name}</div>
                  <div style={{ fontSize: '14px', color: '#64748b' }}>
                    {user.email}
                  </div>
                  <div style={{
                    marginTop: '4px',
                    fontSize: '12px',
                    padding: '4px 8px',
                    background: user.is_admin ? '#dcfce7' : '#f0f9ff',
                    color: user.is_admin ? '#166534' : '#0369a1',
                    borderRadius: '4px',
                    display: 'inline-block'
                  }}>
                    {user.is_admin ? 'Administrator' : 'Employee'}
                  </div>
                </div>
              </div>
              {user.last_login && (
                <div style={{
                  marginTop: '16px',
                  fontSize: '12px',
                  color: '#94a3b8',
                  paddingTop: '16px',
                  borderTop: '1px solid #e2e8f0'
                }}>
                  Last login: {new Date(user.last_login).toLocaleString()}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;