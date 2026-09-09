import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export const Layout: React.FC = () => {
  return (
    <div className="grid grid-cols-[64px_1fr] md:grid-cols-[220px_1fr] h-screen bg-[#0B1418] text-[#DCE7EA] font-sans">
      <Sidebar />
      <div className="overflow-y-auto px-6 py-6 md:px-8 md:py-8">
        <Outlet />
      </div>
    </div>
  );
};
