import React from 'react';
import { NavLink } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center justify-center md:justify-start gap-3 px-4 py-2.5 my-1 text-[#7C9199] hover:text-[#DCE7EA] hover:bg-white/5 border-l-2 transition-colors ${
      isActive ? 'text-[#DCE7EA] border-brand-cyan bg-brand-cyan/10' : 'border-transparent'
    }`;

  return (
    <div className="bg-[#0D1920] border-r border-[#1E3038] flex flex-col py-4">
      <div className="flex items-center justify-center md:justify-start gap-2.5 px-4 pb-5 border-b border-[#1E3038] mb-4">
        <div className="w-6 h-6 rounded border border-[#1E3038] bg-gradient-to-br from-brand-cyan to-[#237871] shrink-0"></div>
        <div className="hidden md:block font-semibold text-[15px] leading-tight">
          ULPF
          <small className="block text-[11px] text-[#7C9199] font-normal">Vendor Portal</small>
        </div>
      </div>

      <NavLink to="/dashboard" className={navItemClass}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 opacity-80 group-hover:opacity-100">
          <path d="M2 4h4v8H2zM10 4h4v4h-4zM10 10h4v2h-4z" fill="currentColor" />
        </svg>
        <span className="hidden md:inline text-[13.5px]">Overview</span>
      </NavLink>

      <NavLink to="/sources" className={navItemClass}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 opacity-80 group-hover:opacity-100">
          <rect x="2" y="3" width="12" height="10" rx="1" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5 8h6M5 10h3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
        <span className="hidden md:inline text-[13.5px]">Sources</span>
      </NavLink>

      <NavLink to="/onboarding" className={navItemClass}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 opacity-80 group-hover:opacity-100">
          <path d="M2 8h4l1.5-4L9.5 12 11 8h3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span className="hidden md:inline text-[13.5px]">Studio</span>
      </NavLink>

      <NavLink to="/rules" className={navItemClass}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 opacity-80 group-hover:opacity-100">
          <rect x="2" y="3" width="12" height="3" rx="1" stroke="currentColor" strokeWidth="1.4" />
          <rect x="2" y="7.5" width="12" height="3" rx="1" stroke="currentColor" strokeWidth="1.4" />
          <rect x="2" y="12" width="12" height="1.5" rx="0.7" stroke="currentColor" strokeWidth="1.4" />
        </svg>
        <span className="hidden md:inline text-[13.5px]">Rule registry</span>
      </NavLink>

      <NavLink to="/jobs" className={navItemClass}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 opacity-80 group-hover:opacity-100">
          <path d="M2 4h12M2 8h12M2 12h7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
        <span className="hidden md:inline text-[13.5px]">Jobs</span>
      </NavLink>

      <NavLink to="/sessions" className={navItemClass}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 opacity-80 group-hover:opacity-100">
          <path d="M2 8a6 6 0 1 1 12 0 6 6 0 0 1-12 0z" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
          <path d="M8 4v4l2.5 1.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
        <span className="hidden md:inline text-[13.5px]">Sessions</span>
      </NavLink>

      <NavLink to="/api-keys" className={navItemClass}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 opacity-80 group-hover:opacity-100">
          <path d="M8 2v8m0 0-3-3m3 3 3-3M3 12v1a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        <span className="hidden md:inline text-[13.5px]">API & keys</span>
      </NavLink>

      <NavLink to="/events" className={navItemClass}>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" className="shrink-0 opacity-80 group-hover:opacity-100">
          <path d="M3 3h10v10H3z" stroke="currentColor" strokeWidth="1.4" />
          <path d="M5.5 6.5h5M5.5 9h3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" />
        </svg>
        <span className="hidden md:inline text-[13.5px]">Log review</span>
      </NavLink>

      <div className="hidden md:block mt-auto px-4 pt-4 border-t border-[#1E3038] text-[12px] text-[#7C9199]">
        <div className="mb-3">
          NTRO Demo Vendor<br />Team S.W.O.R.D.
        </div>
        <button 
          onClick={() => {
            localStorage.removeItem('ulpf_user');
            localStorage.removeItem('ulpf_password');
            window.location.href = '/login';
          }}
          className="text-red-400/80 hover:text-red-300 transition-colors cursor-pointer"
        >
          Sign out
        </button>
      </div>
    </div>
  );
};
