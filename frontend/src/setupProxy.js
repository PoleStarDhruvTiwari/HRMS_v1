// components/EmployeeList.js - Enhanced Version

import React, { useState, useEffect } from "react";
import { employeeAPI } from "../services/api";
import { 
  FaSearch, 
  FaFilter, 
  FaDownload, 
  FaEye,
  FaEdit,
  FaTrash
} from "react-icons/fa";

const EmployeeList = () => {
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [filters, setFilters] = useState({
    department: "",
    status: ""
  });

  useEffect(() => {
    loadEmployees();
  }, []);

  const loadEmployees = async () => {
    try {
      setLoading(true);
      const response = await employeeAPI.getEmployees();
      setEmployees(response.data.items || []);
    } catch (err) {
      setError(err.response?.data?.message || "Failed to load employees");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Filter employees based on search and filters
  const filteredEmployees = employees.filter(emp => {
    const matchesSearch = 
      emp.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      emp.employee_id?.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesDepartment = !filters.department || emp.department === filters.department;
    const matchesStatus = !filters.status || emp.employee_status === filters.status;
    
    return matchesSearch && matchesDepartment && matchesStatus;
  });

  const departments = [...new Set(employees.map(emp => emp.department).filter(Boolean))];
  const statuses = [...new Set(employees.map(emp => emp.employee_status).filter(Boolean))];

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '40px' }}>
        <div className="loading-spinner" style={{ margin: '0 auto 20px' }}></div>
        <p>Loading employees...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card" style={{
        background: '#fef2f2',
        border: '1px solid #fecaca',
        color: '#dc2626'
      }}>
        <h3>Error Loading Employees</h3>
        <p>{error}</p>
        <button 
          className="btn btn-outline" 
          onClick={loadEmployees}
          style={{ marginTop: '20px' }}
        >
          Retry
        </button>
      </div>
    );
  }

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
            Employee Directory
          </h1>
          <p style={{ color: 'var(--text-secondary)', marginTop: '4px' }}>
            Manage and view all employee information
          </p>
        </div>
        <div className="flex gap-4">
          <button className="btn btn-primary">
            + Add Employee
          </button>
          <button className="btn btn-outline">
            <FaDownload /> Export
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="card mb-6">
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '16px',
          alignItems: 'end'
        }}>
          <div>
            <label className="form-label">Search Employees</label>
            <div style={{ position: 'relative' }}>
              <FaSearch style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#94a3b8'
              }} />
              <input
                type="text"
                className="form-input"
                placeholder="Search by name, email, or ID..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ paddingLeft: '40px' }}
              />
            </div>
          </div>
          
          <div>
            <label className="form-label">Department</label>
            <select
              className="form-input"
              value={filters.department}
              onChange={(e) => setFilters({...filters, department: e.target.value})}
            >
              <option value="">All Departments</option>
              {departments.map(dept => (
                <option key={dept} value={dept}>{dept}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="form-label">Status</label>
            <select
              className="form-input"
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
            >
              <option value="">All Status</option>
              {statuses.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>
          
          <button 
            className="btn btn-outline"
            onClick={() => setFilters({ department: "", status: "" })}
            style={{ height: '42px' }}
          >
            <FaFilter /> Clear Filters
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>Total</div>
          <div style={{ fontSize: '24px', fontWeight: '700' }}>{employees.length}</div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>Active</div>
          <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981' }}>
            {employees.filter(e => e.employee_status === 'Active').length}
          </div>
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>Departments</div>
          <div style={{ fontSize: '24px', fontWeight: '700' }}>{departments.length}</div>
        </div>
      </div>

      {/* Employee Table */}
      <div className="card">
        <div className="flex-between mb-4">
          <h3 style={{ fontSize: '18px', fontWeight: '600' }}>
            Employees ({filteredEmployees.length})
          </h3>
          <div className="flex gap-2">
            <button className="btn btn-outline" style={{ padding: '6px 12px' }}>
              <FaEye /> View
            </button>
            <button className="btn btn-outline" style={{ padding: '6px 12px' }}>
              <FaEdit /> Edit
            </button>
          </div>
        </div>

        {filteredEmployees.length === 0 ? (
          <div style={{
            padding: '60px 20px',
            textAlign: 'center',
            color: '#64748b'
          }}>
            <div style={{ fontSize: '48px', opacity: 0.3, marginBottom: '16px' }}>👥</div>
            <h4>No employees found</h4>
            <p style={{ marginTop: '8px' }}>
              {searchTerm || filters.department || filters.status 
                ? 'Try adjusting your search or filters' 
                : 'No employees in the system yet'}
            </p>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table className="professional-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Employee</th>
                  <th>Email</th>
                  <th>Department</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredEmployees.map((emp) => (
                  <tr key={emp.id}>
                    <td style={{ fontWeight: '600' }}>{emp.employee_id}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                          width: '36px',
                          height: '36px',
                          borderRadius: '50%',
                          background: '#e2e8f0',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: '#64748b',
                          fontWeight: '600'
                        }}>
                          {emp.first_name?.[0]}{emp.last_name?.[0]}
                        </div>
                        <div>
                          <div style={{ fontWeight: '500' }}>
                            {emp.first_name} {emp.last_name}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b' }}>
                            {emp.position || 'N/A'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>{emp.personal_email || emp.email || 'N/A'}</td>
                    <td>
                      <span style={{
                        padding: '4px 8px',
                        background: '#f0f9ff',
                        color: '#0369a1',
                        borderRadius: '4px',
                        fontSize: '12px',
                        fontWeight: '500'
                      }}>
                        {emp.department || 'Unassigned'}
                      </span>
                    </td>
                    <td>{emp.role || 'Employee'}</td>
                    <td>
                      <span className={`status-badge status-${emp.employee_status?.toLowerCase() || 'inactive'}`}>
                        {emp.employee_status || 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        <button 
                          className="btn btn-outline"
                          style={{ padding: '6px 12px', fontSize: '12px' }}
                          onClick={() => console.log('View', emp.id)}
                        >
                          <FaEye />
                        </button>
                        <button 
                          className="btn btn-outline"
                          style={{ padding: '6px 12px', fontSize: '12px' }}
                          onClick={() => console.log('Edit', emp.id)}
                        >
                          <FaEdit />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Pagination */}
        {filteredEmployees.length > 0 && (
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginTop: '20px',
            paddingTop: '20px',
            borderTop: '1px solid var(--border-color)'
          }}>
            <div style={{ fontSize: '14px', color: '#64748b' }}>
              Showing {filteredEmployees.length} of {employees.length} employees
            </div>
            <div style={{ display: 'flex', gap: '8px' }}>
              <button className="btn btn-outline" style={{ padding: '6px 12px' }} disabled>
                Previous
              </button>
              <button className="btn btn-outline" style={{ padding: '6px 12px' }}>
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default EmployeeList;