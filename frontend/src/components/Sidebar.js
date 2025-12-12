// components/Sidebar.js

import React from "react";
import { NavLink } from "react-router-dom";
import { 
  FaTachometerAlt, 
  FaUsers, 
  FaCalendarAlt, 
  FaChartBar,
  FaCog,
  FaSignOutAlt,
  FaUserCircle
} from "react-icons/fa";

const Sidebar = () => {
  const user = JSON.parse(localStorage.getItem("user") || "{}");

  const navItems = [
    { path: "/dashboard", icon: <FaTachometerAlt />, label: "Dashboard" },
    { path: "/employees", icon: <FaUsers />, label: "Employees" },
    { path: "/attendance", icon: <FaCalendarAlt />, label: "Attendance" },
    { path: "/reports", icon: <FaChartBar />, label: "Reports" },
    { path: "/settings", icon: <FaCog />, label: "Settings" },
  ];

  return (
    <aside style={{
      width: '240px',
      background: 'white',
      borderRight: '1px solid var(--border-color)',
      display: 'flex',
      flexDirection: 'column',
      padding: '20px 0'
    }}>
      {/* User Profile */}
      <div style={{
        padding: '20px',
        borderBottom: '1px solid var(--border-color)',
        marginBottom: '20px'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '12px'
        }}>
          {user.picture ? (
            <img 
              src={user.picture} 
              alt={user.name}
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                objectFit: 'cover'
              }}
            />
          ) : (
            <FaUserCircle size={40} color="#64748b" />
          )}
          <div>
            <div style={{
              fontWeight: '600',
              fontSize: '14px'
            }}>
              {user.name || 'User'}
            </div>
            <div style={{
              fontSize: '12px',
              color: '#64748b'
            }}>
              {user.is_admin ? 'Administrator' : 'Employee'}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1 }}>
        <ul style={{ listStyle: 'none' }}>
          {navItems.map((item) => (
            <li key={item.path} style={{ marginBottom: '4px' }}>
              <NavLink
                to={item.path}
                style={({ isActive }) => ({
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 20px',
                  color: isActive ? 'var(--primary-color)' : 'var(--text-primary)',
                  background: isActive ? '#eff6ff' : 'transparent',
                  borderRight: isActive ? '3px solid var(--primary-color)' : 'none',
                  textDecoration: 'none',
                  fontSize: '14px',
                  fontWeight: '500',
                  transition: 'all 0.2s'
                })}
              >
                <span style={{ fontSize: '16px' }}>{item.icon}</span>
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Logout Button */}
      <div style={{ padding: '20px', borderTop: '1px solid var(--border-color)' }}>
        <button
          onClick={() => {
            localStorage.clear();
            window.location.href = "/login";
          }}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            padding: '12px 20px',
            width: '100%',
            background: 'transparent',
            border: '1px solid var(--border-color)',
            borderRadius: '6px',
            color: '#64748b',
            fontSize: '14px',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          <FaSignOutAlt />
          Sign Out
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;