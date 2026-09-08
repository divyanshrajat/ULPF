import React from 'react';
import { NavLink } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  return (
    <div className="side">
      <div className="brand">
        <div className="brand-mark"></div>
        <div className="brand-name">
          ULPF<small>Vendor Portal</small>
        </div>
      </div>

      <NavLink to="/onboarding" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 8h4l1.5-4L9.5 12 11 8h3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>Studio</span>
      </NavLink>

      <NavLink to="/rules" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="2" y="3" width="12" height="3" rx="1" stroke="currentColor" strokeWidth="1.4" />
          <rect x="2" y="7.5" width="12" height="3" rx="1" stroke="currentColor" strokeWidth="1.4" />
          <rect x="2" y="12" width="12" height="1.5" rx="0.7" stroke="currentColor" strokeWidth="1.4" />
        </svg>
        <span>Rule registry</span>
      </NavLink>

      <NavLink to="/jobs" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M2 4h12M2 8h12M2 12h7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
        <span>Jobs & sessions</span>
      </NavLink>

      <NavLink to="/api-keys" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 2v8m0 0-3-3m3 3 3-3M3 12v1a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span>API & keys</span>
      </NavLink>

      <NavLink to="/events" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M3 3h10v10H3z" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5.5 6.5h5M5.5 9h3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
        <span>Log review</span>
      </NavLink>

      <div className="side-foot">
        NTRO Demo Vendor<br />Environment: Sandbox
      </div>
    </div>
  );
};
