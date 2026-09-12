import React from 'react';
import { NavLink } from 'react-router-dom';

export const TopNav: React.FC = () => {
  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-2 px-4 h-full text-[13px] font-bold border-b-[3px] transition-colors ${
      isActive 
        ? 'text-[#062744] border-[#C89B3C] bg-slate-50' 
        : 'text-slate-500 border-transparent hover:text-[#062744] hover:bg-slate-50'
    }`;

  return (
    <div className="bg-white text-slate-900 h-16 md:h-[72px] relative z-50 shadow-sm">
      <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-slate-200" />
      <div className="flex items-center px-4 md:px-6 h-full">
        <div className="flex items-center gap-3 mr-8 md:mr-16 h-full py-2">
          <img src="/assets/ulpf_logo.png" alt="ULPF Logo" className="h-full w-auto object-contain drop-shadow-sm" />
          <div className="flex flex-col justify-center">
            <span className="text-[20px] md:text-[24px] font-extrabold text-[#062744] tracking-tight leading-none mb-0.5">ULPF</span>
            <span className="text-[7px] md:text-[9px] font-bold text-[#062744] tracking-wide mb-1">Universal Log Pre-processing Framework</span>
            <div className="flex items-center">
              <div className="h-[1.5px] w-3 md:w-4 bg-[#C89B3C] mr-1.5"></div>
              <span className="text-[6px] md:text-[8px] text-[#1769D5] italic font-medium">Different Logs. <span className="text-[#C89B3C] font-bold">One Framework.</span></span>
            </div>
          </div>
        </div>
        
        <nav className="flex items-center overflow-x-auto no-scrollbar h-full">
          <NavLink to="/dashboard" className={navItemClass}>
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"/></svg>
            Overview
          </NavLink>
          <NavLink to="/sources" className={navItemClass}>
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"/></svg>
            Sources
          </NavLink>
          <NavLink to="/onboarding" className={navItemClass}>
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
            Studio
          </NavLink>
          <NavLink to="/rules" className={navItemClass}>
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
            Rules
          </NavLink>
          <NavLink to="/jobs" className={navItemClass}>
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            Jobs
          </NavLink>
          <NavLink to="/sessions" className={navItemClass}>
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
            Sessions
          </NavLink>
          <NavLink to="/api-keys" className={navItemClass}>
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"/></svg>
            API & Keys
          </NavLink>
          <NavLink to="/events" className={navItemClass}>
            <svg className="w-[18px] h-[18px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2"><path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
            Log Review
          </NavLink>
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
