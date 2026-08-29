import { Card } from '../components/ui/Card';
import { Settings, HardDrive, Cpu, AlertTriangle, Key, Zap } from 'lucide-react';
import { useState } from 'react';

export function System() {
  const [retention, setRetention] = useState('90');
  const [fastPath, setFastPath] = useState(true);

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Settings className="w-6 h-6 text-brand-cyan" />
            System Configuration
          </h1>
          <p className="text-slate-400 mt-1">Manage global middleware settings, storage policies, and AI inference options.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Core Processing Engine */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <Cpu className="w-5 h-5 text-brand-cyan" />
            <h2 className="text-lg font-semibold text-slate-100">Processing Engine</h2>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-slate-200 font-medium">Deterministic Fast Path</div>
                <div className="text-sm text-slate-400">Bypass ML inference for known templates</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" checked={fastPath} onChange={() => setFastPath(!fastPath)} />
                <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-cyan"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <div className="text-slate-200 font-medium">Strict OCSF Validation</div>
                <div className="text-sm text-slate-400">Drop events missing required schema fields</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" />
                <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-cyan"></div>
              </label>
            </div>
          </div>
        </Card>

        {/* Data Retention & Storage */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <HardDrive className="w-5 h-5 text-brand-purple" />
            <h2 className="text-lg font-semibold text-slate-100">Storage & Retention</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <label className="block text-slate-200 font-medium mb-1">Raw Vault Retention (Days)</label>
              <div className="text-sm text-slate-400 mb-2">Duration to keep original immutable payloads.</div>
              <select 
                value={retention}
                onChange={(e) => setRetention(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-slate-200 focus:outline-none focus:ring-1 focus:ring-brand-purple"
              >
                <option value="30">30 Days</option>
                <option value="90">90 Days</option>
                <option value="180">180 Days</option>
                <option value="365">1 Year</option>
                <option value="forever">Indefinite (Requires Admin)</option>
              </select>
            </div>
            
            <div className="pt-2">
               <div className="flex items-center justify-between text-sm mb-1">
                 <span className="text-slate-400">Disk Usage (Local Cache)</span>
                 <span className="text-slate-200">1.2 TB / 2.0 TB</span>
               </div>
               <div className="w-full bg-slate-800 rounded-full h-2">
                  <div className="bg-brand-purple h-2 rounded-full" style={{ width: '60%' }}></div>
               </div>
            </div>
          </div>
        </Card>

        {/* AI & Telemetry */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <Zap className="w-5 h-5 text-brand-amber" />
            <h2 className="text-lg font-semibold text-slate-100">AI Model Configuration</h2>
          </div>
          
          <div className="space-y-4">
            <div>
               <div className="text-slate-200 font-medium">Local Model Weights</div>
               <div className="text-sm text-slate-400">Current semantic matching model version.</div>
               <div className="mt-2 p-2 bg-slate-900 border border-slate-800 rounded flex items-center justify-between">
                 <span className="text-xs font-mono text-brand-amber">v2.4.1-alpha (Air-gapped)</span>
                 <button className="text-xs text-brand-cyan hover:underline">Check Updates</button>
               </div>
            </div>
            
            <div className="flex items-center justify-between pt-2">
              <div>
                <div className="text-slate-200 font-medium">Telemetry Sharing</div>
                <div className="text-sm text-slate-400">Send anonymized drift metrics to central server</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" className="sr-only peer" />
                <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-cyan"></div>
              </label>
            </div>
          </div>
        </Card>

        {/* Access & Security */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <Key className="w-5 h-5 text-brand-green" />
            <h2 className="text-lg font-semibold text-slate-100">API & Security</h2>
          </div>
          
          <div className="space-y-4">
             <div>
               <div className="text-slate-200 font-medium">Global API Keys</div>
               <div className="text-sm text-slate-400 mb-2">Used for downstream SIEM integration.</div>
               <div className="flex gap-2">
                 <input type="password" value="************************" readOnly className="flex-1 bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-slate-400 text-sm focus:outline-none" />
                 <button className="px-3 py-2 bg-slate-800 hover:bg-slate-700 rounded-md text-sm text-slate-200 border border-slate-700 transition-colors">Regenerate</button>
               </div>
             </div>
             
             <div className="mt-4 p-3 bg-brand-amber/10 border border-brand-amber/20 rounded-md flex items-start gap-3">
               <AlertTriangle className="w-5 h-5 text-brand-amber shrink-0 mt-0.5" />
               <div>
                 <h4 className="text-sm font-medium text-brand-amber">Air-gapped Environment</h4>
                 <p className="text-xs text-brand-amber/80 mt-1">External SSO and telemetry are disabled per network constraints.</p>
               </div>
             </div>
          </div>
        </Card>

      </div>
    </div>
  );
}
