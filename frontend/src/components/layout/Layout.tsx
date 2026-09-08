import React from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';

export const Layout: React.FC = () => {
  return (
    <div className="shell">
      <Sidebar />
      <div className="main">
        <Outlet />
      </div>
    </div>
  );
};
