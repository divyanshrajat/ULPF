import React, { useEffect, useState } from 'react';
import { fetchRules, updateRuleLifecycle } from '../services/api';
import { FileText, Plus } from 'lucide-react';
import { Button } from '../components/ui/Button';
import { parseToDate, formatIST } from '../utils/date';

export const Rules: React.FC = () => {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadRules = async () => {
    try {
      const data = await fetchRules();
      let arr = Array.isArray(data) ? data : (data as any).items || [];
      arr.sort((a: any, b: any) => (parseToDate(b.updated_at)?.getTime() || 0) - (parseToDate(a.updated_at)?.getTime() || 0));
      setRules(arr);
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
          <h1 className="text-2xl font-bold text-slate-900 mb-1 font-serif">Rule registry</h1>
          <p className="text-slate-600 text-sm">Every rule your team has authored, versioned and lifecycle-managed.</p>
        </div>
      </div>
      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-md">
        <div className="flex flex-wrap gap-4 mb-5 text-[12px] text-slate-600">
          <span><b className="text-slate-900 font-semibold">Active</b> — auto-detect + explicit calls</span>
          <span><b className="text-slate-900 font-semibold">Deprecated</b> — explicit calls only</span>
          <span><b className="text-slate-900 font-semibold">Disabled</b> — rejected even if called</span>
          <span><b className="text-slate-900 font-semibold">Archived</b> — history only, not invokable</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12.8px] border-collapse">
            <thead>
              <tr>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Rule ID</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Schema</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Status</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Updated</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">State</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={5} className="p-8 text-center text-slate-500">Loading rules...</td></tr>
              ) : rules.length === 0 ? (
                <tr>
                  <td colSpan={5} className="p-12 text-center">
                    <FileText className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                    <h3 className="text-lg font-bold text-slate-700">No rules authored yet</h3>
                    <p className="text-sm text-slate-500 mt-1 mb-4 max-w-sm mx-auto">
                      Head over to the Studio to analyze logs and draft your first rule.
                    </p>
                    <Button
                      size="sm"
                      onClick={() => (window.location.href = '/onboarding')}
                      className="bg-brand-cyan text-white hover:brightness-110 font-bold"
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
                    <tr key={f.id} className="hover:bg-white/5 transition-colors border-b border-slate-200 last:border-0">
                      <td className="py-2.5 px-2.5 font-mono text-slate-900">{f.name}@{f.version}</td>
                      <td className="py-2.5 px-2.5 text-slate-700">{f.target_schema}</td>
                      <td className="py-2.5 px-2.5 text-slate-700">{f.status}</td>
                      <td className="py-2.5 px-2.5 text-slate-600">
                        {formatIST(f.updated_at)}
                      </td>
                      <td className="py-2.5 px-2.5">
                        <select 
                          className="bg-slate-50 border border-slate-200 text-slate-900 rounded px-2 py-1 outline-none text-xs"
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
