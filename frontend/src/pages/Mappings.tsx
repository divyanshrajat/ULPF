import { Card } from '../components/ui/Card';
import { Search, Filter, ShieldCheck, AlertTriangle } from 'lucide-react';

export function Mappings() {
  const mappings = [
    { id: 'MAP-001', source: 'Firewall-X', rawField: 'src_ip', targetField: 'source.ip', confidence: 98, status: 'Approved' },
    { id: 'MAP-002', source: 'Firewall-X', rawField: 'dst_ip', targetField: 'destination.ip', confidence: 96, status: 'Approved' },
    { id: 'MAP-003', source: 'Windows-DC', rawField: 'EventID', targetField: 'activity_id', confidence: 85, status: 'Review Needed' },
    { id: 'MAP-004', source: 'Windows-DC', rawField: 'LogonType', targetField: 'logon_type_id', confidence: 92, status: 'Approved' },
    { id: 'MAP-005', source: 'Okta-Auth', rawField: 'actor.id', targetField: 'actor.user.uuid', confidence: 99, status: 'Approved' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Mappings Explorer</h1>
          <p className="text-slate-400 mt-1">Browse and manage semantic field mappings across all sources.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search mappings..." 
              className="bg-slate-900 border border-slate-800 rounded-md pl-9 pr-4 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-cyan"
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 text-sm font-medium text-slate-200 transition-colors">
            <Filter className="w-4 h-4" />
            Filter
          </button>
        </div>
      </div>

      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4 font-medium">Source</th>
                <th className="px-6 py-4 font-medium">Raw Field</th>
                <th className="px-6 py-4 font-medium">Target Schema Field</th>
                <th className="px-6 py-4 font-medium">Confidence</th>
                <th className="px-6 py-4 font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {mappings.map((map) => (
                <tr key={map.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-medium text-slate-200">{map.source}</td>
                  <td className="px-6 py-4 font-mono text-xs text-brand-purple">{map.rawField}</td>
                  <td className="px-6 py-4 font-mono text-xs text-brand-cyan">{map.targetField}</td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-slate-800 rounded-full h-1.5">
                        <div 
                          className="bg-brand-cyan h-1.5 rounded-full" 
                          style={{ width: `${map.confidence}%` }}
                        />
                      </div>
                      <span className="text-xs text-slate-400">{map.confidence}%</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {map.status === 'Approved' ? (
                      <span className="flex items-center gap-1.5 text-brand-green text-xs font-medium">
                        <ShieldCheck className="w-3.5 h-3.5" /> Approved
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-brand-amber text-xs font-medium">
                        <AlertTriangle className="w-3.5 h-3.5" /> Review Needed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
