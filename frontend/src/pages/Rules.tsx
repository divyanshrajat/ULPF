import React, { useEffect, useState } from 'react';
import { fetchRules, updateRuleLifecycle } from '../services/api';
import { FileText, Plus } from 'lucide-react';
import { Button } from '../components/ui/Button';

export const Rules: React.FC = () => {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadRules = async () => {
    try {
      const data = await fetchRules();
      setRules(Array.isArray(data) ? data : (data as any).items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const changeState = async (ruleId: string, newState: string) => {
    try {
      if (newState === 'Active') {
        await updateRuleLifecycle(ruleId, { action: 'approve' });
      } else if (newState === 'Disabled') {
        await updateRuleLifecycle(ruleId, { action: 'reject' });
      }
      loadRules();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-6xl mx-auto pb-12">
      <div className="flex justify-between items-start mb-6 flex-wrap gap-2.5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Rule registry</h1>
          <p className="text-slate-400 text-sm">Every rule your team has authored, versioned and lifecycle-managed.</p>
        </div>
        <div className="font-mono text-[11px] text-brand-amber border border-brand-amber/35 rounded bg-brand-amber/5 px-2.5 py-1 whitespace-nowrap">
          SANDBOX
        </div>
      </div>
      <div className="bg-[#101D24] border border-[#1E3038] rounded-xl p-6 shadow-md">
        <div className="flex flex-wrap gap-4 mb-5 text-[12px] text-slate-400">
          <span><b className="text-slate-100 font-semibold">Active</b> — auto-detect + explicit calls</span>
          <span><b className="text-slate-100 font-semibold">Deprecated</b> — explicit calls only</span>
          <span><b className="text-slate-100 font-semibold">Disabled</b> — rejected even if called</span>
          <span><b className="text-slate-100 font-semibold">Archived</b> — history only, not invokable</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12.8px] border-collapse">
            <thead>
              <tr>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Rule ID</th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Schema</th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Status</th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Updated</th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">State</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="p-8 text-center text-slate-500">Loading rules...</td></tr>
              ) : rules.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center">
                    <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <h3 className="text-lg font-bold text-slate-300">No rules authored yet</h3>
                    <p className="text-sm text-slate-500 mt-1 mb-4 max-w-sm mx-auto">
                      Head over to the Studio to analyze logs and draft your first rule.
                    </p>
                    <Button
                      size="sm"
                      onClick={() => (window.location.href = '/onboarding')}
                      className="bg-brand-cyan text-[#062024] hover:bg-[#32b2ac] font-bold"
                    >
                      <Plus className="w-4 h-4 mr-1.5" />
                      Go to Studio
                    </Button>
                  </td>
                </tr>
              ) : (
                rules.map((f) => {
                  const uiState = f.status === 'ACTIVE' ? 'Active' : f.status === 'REJECTED' ? 'Disabled' : 'Archived';
                  
                  return (
                    <tr key={f.id} className="hover:bg-white/5 transition-colors border-b border-[#1E3038] last:border-0">
                      <td className="py-2.5 px-2.5 font-mono text-brand-cyan">{f.name}@{f.version}</td>
                      <td className="py-2.5 px-2.5 text-slate-300">{f.target_schema}</td>
                      <td className="py-2.5 px-2.5 text-slate-300">{f.status}</td>
                      <td className="py-2.5 px-2.5 text-slate-400">{new Date(f.updated_at).toISOString().split('T')[0]}</td>
                      <td className="py-2.5 px-2.5">
                        <select 
                          className="bg-[#0D1920] border border-[#1E3038] text-[#DCE7EA] rounded px-2 py-1 outline-none text-xs"
                          value={uiState}
                          onChange={(e) => changeState(f.id, e.target.value)}
                        >
                          <option value="Active">Active</option>
                          <option value="Deprecated">Deprecated</option>
                          <option value="Disabled">Disabled</option>
                          <option value="Archived">Archived</option>
                        </select>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
