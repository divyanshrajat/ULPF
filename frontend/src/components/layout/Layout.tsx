import React from 'react';
import { Outlet } from 'react-router-dom';
import { TopNav } from './TopNav';

export const Layout: React.FC = () => {
  return (
    <div className="flex flex-col h-screen bg-slate-50 text-slate-900 font-sans">
      <TopNav />
      <div className="flex-1 overflow-y-auto px-6 py-6 md:px-8 md:py-8 bg-slate-50">
        <Outlet />
      </div>
    </div>
  );
};
