import React from 'react';
import { Outlet } from 'react-router-dom';
import { TopNav } from './TopNav';

export const Layout: React.FC = () => {
  return (
    <div 
      className="flex flex-col h-screen text-slate-900 font-sans relative overflow-hidden bg-slate-50"
      style={{ 
        backgroundImage: "url('/assets/layout_bg.png')",
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }}
    >
      {/* Main Content Area */}
      <div className="relative z-20 flex flex-col h-full w-full bg-white/40">
        <TopNav />
        <div className="flex-1 overflow-y-auto px-6 py-6 md:px-12 md:py-8">
          <Outlet />
        </div>
        <footer className="w-full bg-white/80 backdrop-blur-md border-t border-slate-200 py-2.5 px-4 shrink-0 shadow-[0_-2px_10px_rgba(0,0,0,0.02)]">
          <div className="flex justify-center items-center text-[10.5px] font-bold text-slate-400 tracking-widest uppercase">
            Adaptive &nbsp;&nbsp;&middot;&nbsp;&nbsp; Lossless &nbsp;&nbsp;&middot;&nbsp;&nbsp; Traceable &nbsp;&nbsp;&middot;&nbsp;&nbsp; Schema-Evolving &nbsp;&nbsp;&middot;&nbsp;&nbsp; Analytics-Ready &nbsp;&nbsp;&middot;&nbsp;&nbsp; Air-Gapped &nbsp;&nbsp;&middot;&nbsp;&nbsp; Scalable
          </div>
        </footer>
      </div>
    </div>
  );
};
