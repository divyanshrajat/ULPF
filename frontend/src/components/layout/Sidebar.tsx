import { NavLink } from 'react-router-dom';
import { 
  Activity, 
  Server, 
  FileUp, 
  Workflow, 
  CheckSquare, 
  Database, 
  Search, 
  Network, 
  BookOpen, 
  ShieldCheck, 
  Settings 
} from 'lucide-react';

const primaryTabs = [
  { id: 'dashboard', label: 'Overview', path: '/', icon: Activity },
  { id: 'sources', label: 'Sources', path: '/sources', icon: Server },
  { id: 'onboarding', label: 'Onboarding', path: '/onboarding', icon: FileUp },
  { id: 'processing', label: 'Processing', path: '/processing', icon: Workflow },
  { id: 'review', label: 'Review', path: '/review', icon: CheckSquare },
  { id: 'events', label: 'Events', path: '/events', icon: Database },
  { id: 'trace', label: 'Trace Explorer', path: '/trace', icon: Search },
];

const adminTabs = [
  { id: 'mappings', label: 'Mappings', path: '/mappings', icon: Network },
  { id: 'schemas', label: 'Schemas', path: '/schemas', icon: BookOpen },
  { id: 'vault', label: 'Raw Vault', path: '/vault', icon: ShieldCheck },
  { id: 'system', label: 'System', path: '/system', icon: Settings },
];

function NavItem({ tab }: { tab: any }) {
  return (
    <li>
      <NavLink
        to={tab.path}
        className={({ isActive }) =>
          `flex items-center w-full text-left px-3 py-2 rounded-md transition-colors text-sm font-medium ${
            isActive ? 'bg-slate-800 text-brand-cyan' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-100'
          }`
        }
      >
        <tab.icon className="w-4 h-4 mr-3" />
        {tab.label}
      </NavLink>
    </li>
  );
}

export function Sidebar() {
  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0">
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <h1 className="text-xl font-bold text-slate-100 tracking-widest flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-brand-cyan flex items-center justify-center">
            <span className="text-slate-950 font-black text-xs">U</span>
          </div>
          ULPF
        </h1>
      </div>
      <nav className="flex-1 py-4 overflow-y-auto">
        <ul className="space-y-1 px-3">
          {primaryTabs.map((tab) => (
            <NavItem key={tab.id} tab={tab} />
          ))}
        </ul>
        
        <div className="mt-8 mb-4 px-6">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Administration</h3>
        </div>
        
        <ul className="space-y-1 px-3">
          {adminTabs.map((tab) => (
            <NavItem key={tab.id} tab={tab} />
          ))}
        </ul>
      </nav>
      
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 px-2">
          <div className="w-8 h-8 rounded-full bg-slate-800 flex items-center justify-center text-slate-300">
            SO
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="text-sm font-medium text-slate-200 truncate">System Operator</p>
            <p className="text-xs text-slate-500 truncate">Admin</p>
          </div>
        </div>
      </div>
    </aside>
  );
}
