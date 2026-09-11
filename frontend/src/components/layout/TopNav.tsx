import React from 'react';
import { NavLink } from 'react-router-dom';

export const TopNav: React.FC = () => {
  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center px-4 h-full text-sm font-medium border-b-2 transition-colors ${
      isActive 
        ? 'text-slate-900 border-slate-900 bg-slate-50' 
        : 'text-slate-500 border-transparent hover:text-slate-900 hover:bg-slate-50'
    }`;

  return (
    <div className="bg-white text-slate-900 h-14 relative z-50">
      <div className="absolute bottom-0 left-[240px] right-0 h-[1px] bg-slate-200" />
      <div className="flex items-center px-6 h-full">
        <div className="flex items-center mr-16 md:mr-24 h-full pt-2">
          <img src="/assets/ulpf_logo.png" alt="ULPF Logo" className="h-12 md:h-14 w-auto object-contain scale-[2] md:scale-[2.5] origin-top-left relative z-10" />
        </div>
        
        <nav className="flex items-center overflow-x-auto no-scrollbar h-full">
          <NavLink to="/dashboard" className={navItemClass}>Overview</NavLink>
          <NavLink to="/sources" className={navItemClass}>Sources</NavLink>
          <NavLink to="/onboarding" className={navItemClass}>Studio</NavLink>
          <NavLink to="/rules" className={navItemClass}>Rules</NavLink>
          <NavLink to="/jobs" className={navItemClass}>Jobs</NavLink>
          <NavLink to="/sessions" className={navItemClass}>Sessions</NavLink>
          <NavLink to="/api-keys" className={navItemClass}>API & Keys</NavLink>
          <NavLink to="/events" className={navItemClass}>Log Review</NavLink>
        </nav>
        
        <div className="ml-auto flex items-center gap-4 h-full pl-4 border-l border-slate-200">
          <div className="text-xs text-slate-500 hidden lg:block text-right">
            <div>NTRO Demo Vendor</div>
            <div className="text-slate-900 font-medium">Team S.W.O.R.D.</div>
          </div>
          <button
            onClick={() => {
              sessionStorage.removeItem('ulpf_user');
              sessionStorage.removeItem('ulpf_password');
              window.location.href = '/login';
            }}
            className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center text-sm font-bold text-slate-700 hover:bg-slate-200 transition-colors"
            title="Sign out"
          >
            TS
          </button>
        </div>
      </div>
    </div>
  );
};
