import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Search, Bell } from 'lucide-react';
import { Button } from '../ui/Button';
import { useSourceContext } from '../../contexts/SourceContext';

export function Layout() {
  const { currentSource, setCurrentSource } = useSourceContext();
  
  return (
    <div className="flex h-screen bg-slate-950 text-slate-300 font-sans overflow-hidden selection:bg-brand-cyan/30">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center px-6 justify-between shrink-0">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 relative">
              <span className="text-sm font-medium text-slate-400">Source:</span>
              <select 
                className="appearance-none bg-slate-800 hover:bg-slate-700 text-slate-100 text-sm font-semibold rounded-md border border-slate-700 px-3 py-1.5 pr-8 transition-colors focus:outline-none focus:ring-1 focus:ring-brand-cyan cursor-pointer"
                value={currentSource ? currentSource.id : "all"}
                onChange={(e) => {
                  if (e.target.value === "all") {
                    setCurrentSource(null);
                  } else {
                    setCurrentSource({
                      id: "SRC-FIREWALLX-001",
                      name: "Firewall-X",
                      vendor: "Cisco",
                      product: "ASA"
                    });
                  }
                }}
              >
                <option value="all">All Sources</option>
                <option value="SRC-FIREWALLX-001">Firewall-X</option>
              </select>
              <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-2 text-slate-400">
                <span className="text-xs">▾</span>
              </div>
            </div>
            <div className="h-4 w-px bg-slate-700 mx-2" />
            <div className="relative group">
              <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-brand-cyan transition-colors" />
              <input 
                type="text" 
                placeholder="Search traces, events, mappings..." 
                className="bg-slate-950 border border-slate-800 rounded-md pl-9 pr-4 py-1.5 text-sm focus:outline-none focus:ring-1 focus:ring-brand-cyan focus:border-brand-cyan w-64 transition-all text-slate-100 placeholder:text-slate-600"
              />
            </div>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm">
              <div className="w-2 h-2 rounded-full bg-brand-green animate-pulse" />
              <span className="text-slate-300">Operational</span>
            </div>
            <Button variant="ghost" size="icon" className="relative text-slate-400 hover:text-slate-100">
              <Bell className="w-5 h-5" />
              <span className="absolute top-2 right-2 w-2 h-2 rounded-full bg-brand-amber border-2 border-slate-900" />
            </Button>
          </div>
        </header>
        <div className="flex-1 overflow-auto bg-slate-950 p-6">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
