import React from "react";
import { Link, useLocation } from "react-router-dom";

const Navbar = () => {
  const location = useLocation();
  const isLoggedIn = localStorage.getItem("access_token");

  return (
    <nav style={{
      background: "#2563eb",
      color: "white",
      padding: "15px 0",
      marginBottom: "20px"
    }}>
      <div className="container" style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center"
      }}>
        <div style={{ fontSize: "20px", fontWeight: "bold" }}>
          <Link to="/" style={{ color: "white", textDecoration: "none" }}>
            HRMS System
          </Link>
        </div>
        
        <div style={{ display: "flex", gap: "20px" }}>
          {isLoggedIn ? (
            <>
              <Link 
                to="/dashboard" 
                style={{
                  color: "white",
                  textDecoration: location.pathname === "/dashboard" ? "underline" : "none"
                }}
              >
                Dashboard
              </Link>
              <Link 
                to="/employees" 
                style={{
                  color: "white",
                  textDecoration: location.pathname === "/employees" ? "underline" : "none"
                }}
              >
                Employees
              </Link>
            </>
          ) : (
            <Link 
              to="/login" 
              style={{
                color: "white",
                textDecoration: location.pathname === "/login" ? "underline" : "none"
              }}
            >
              Login
            </Link>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
