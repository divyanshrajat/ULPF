import React, { useEffect, useState } from 'react';
import { fetchEvents } from '../services/api';
import { FileSearch, ChevronRight, ChevronDown } from 'lucide-react';

export const Events: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [masked, setMasked] = useState(true);
  const [openDetail, setOpenDetail] = useState<number | null>(null);

  useEffect(() => {
    const loadEvents = async () => {
      try {
        const data = await fetchEvents({ page_size: 50 });
        setEvents(data.items || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadEvents();
  }, []);

  const toggleDetail = (index: number) => {
    setOpenDetail(openDetail === index ? null : index);
  };

  return (
    <div className="max-w-6xl mx-auto pb-12">
      <div className="flex justify-between items-start mb-6 flex-wrap gap-2.5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Log review</h1>
          <p className="text-slate-400 text-sm">Every raw event, its normalized output, and the exact rule used.</p>
        </div>
        <div className="font-mono text-[11px] text-brand-amber border border-brand-amber/35 rounded bg-brand-amber/5 px-2.5 py-1 whitespace-nowrap">
          SANDBOX
        </div>
      </div>

      <div className="bg-[#101D24] border border-[#1E3038] rounded-xl p-6 shadow-md">
        <div className="flex justify-between items-center mb-5 pb-5 border-b border-[#1E3038] flex-wrap gap-3">
          <div className="text-[13px] text-slate-400 m-0">Click a row to inspect raw vs. normalized.</div>
          <label className="flex items-center gap-2 text-[13px] text-slate-300 font-medium cursor-pointer hover:text-white transition-colors">
            <input 
              type="checkbox" 
              className="w-4 h-4 accent-brand-cyan cursor-pointer rounded border-[#1E3038] bg-[#0D1920]"
              checked={masked} 
              onChange={(e) => setMasked(e.target.checked)} 
            />
            Mask sensitive fields
          </label>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12.8px] border-collapse">
            <thead>
              <tr>
                <th className="w-8 py-2 border-b border-[#1E3038]"></th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Timestamp</th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Source</th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Rule used</th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Status</th>
                <th className="text-slate-400 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-[#1E3038]">Trace UUID</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="p-8 text-center text-slate-500">Loading events...</td></tr>
              ) : events.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center">
                    <FileSearch className="w-10 h-10 text-slate-600 mx-auto mb-3" />
                    <h3 className="text-[15px] font-bold text-slate-300">No events recorded</h3>
                    <p className="text-[13px] text-slate-500 mt-1 max-w-sm mx-auto">Push logs via the API to see them appear here.</p>
                  </td>
                </tr>
              ) : (
                events.map((e, i) => {
                  const ts = new Date(e.created_at).toLocaleString();
                  const source = e.source_id || 'unknown';
                  const ruleId = e.rule_id || '—';
                  const status = e.processing_path === 'fast' ? 'ok' : 'unresolved';
                  
                  let statusBadge;
                  if (status === 'ok') statusBadge = <span className="inline-block text-[11px] font-mono px-2 py-0.5 rounded-full border bg-brand-green/10 text-brand-green border-brand-green/35">normalized</span>;
                  else statusBadge = <span className="inline-block text-[11px] font-mono px-2 py-0.5 rounded-full border bg-brand-amber/10 text-brand-amber border-brand-amber/35">adaptive (spot-check)</span>;

                  return (
                    <React.Fragment key={e.id || i}>
                      <tr 
                        className={`cursor-pointer transition-colors border-b border-[#1E3038] last:border-0 ${openDetail === i ? 'bg-white/5' : 'hover:bg-white-[0.03]'}`} 
                        onClick={() => toggleDetail(i)}
                      >
                        <td className="py-2.5 text-slate-500 text-center">
                          {openDetail === i ? <ChevronDown className="w-4 h-4 mx-auto" /> : <ChevronRight className="w-4 h-4 mx-auto" />}
                        </td>
                        <td className="py-2.5 px-2.5 font-mono text-slate-300">{ts}</td>
                        <td className="py-2.5 px-2.5 text-slate-300">{source}</td>
                        <td className="py-2.5 px-2.5 font-mono text-brand-cyan">{ruleId}</td>
                        <td className="py-2.5 px-2.5">{statusBadge}</td>
                        <td className="py-2.5 px-2.5 font-mono text-slate-400 text-xs">{e.trace_id?.slice(0, 8) || '—'}</td>
                      </tr>
                      {openDetail === i && (
                        <tr className="bg-[#091217]">
                          <td colSpan={6} className="p-0 border-b border-[#1E3038]">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-5">
                              <div>
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Raw event</label>
                                <div className="bg-[#0D1920] border border-[#1E3038] rounded-lg p-3 whitespace-pre-wrap word-break text-slate-300 max-h-60 overflow-auto font-mono text-[11.5px]">
                                  {masked && e.masked_payload ? JSON.stringify(e.masked_payload, null, 2) : JSON.stringify(e.raw_payload || {}, null, 2)}
                                </div>
                              </div>
                              <div>
                                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Normalized</label>
                                <div className="bg-[#0D1920] border border-[#1E3038] rounded-lg p-3 whitespace-pre-wrap word-break text-brand-cyan max-h-60 overflow-auto font-mono text-[11.5px]">
                                  {JSON.stringify(e.normalized_payload || {}, null, 2)}
                                </div>
                                <div className="mt-3 text-[11.5px] font-mono text-slate-500">
                                  raw <b className="text-slate-300 font-semibold">{e.trace_id?.slice(0, 8) || '—'}</b> → rule <b className="text-brand-cyan font-semibold">{ruleId}</b> → normalized <b className="text-slate-300 font-semibold">{e.trace_id?.slice(0, 8) || '—'}-n</b>
                                </div>
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
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
