import React, { useEffect, useState } from 'react';
import { fetchSessions } from '../services/api';
import { Activity } from 'lucide-react';
import { formatIST } from '../utils/date';

export const Sessions: React.FC = () => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const sessionsRes = await fetchSessions();
        setSessions(sessionsRes.items || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const renderEventStrip = (lock: any, isStreaming: boolean) => {
    if (!lock) return null;
    const blocks = [];
    
    const detectCount = Math.min(lock.sample_count_seen || 0, 5);
    for (let i = 0; i < detectCount; i++) {
      blocks.push(<div key={`d-${i}`} className="ev detect" title="detecting">{i + 1}</div>);
    }
    
    if (lock.status === 'LOCKED') {
      blocks.push(<div key="l1" className="ev lock" title="locked">…</div>);
      if (isStreaming) {
        blocks.push(<div key="s1" className="ev spot" title="spot-check ok">•</div>);
        blocks.push(<div key="l2" className="ev lock" title="locked">…</div>);
        
        if (lock.mismatch_count > 0) {
           blocks.push(<div key="u1" className="ev unresolved" title="spot-check mismatch">!</div>);
           blocks.push(<div key="l3" className="ev lock" title="locked">…</div>);
           blocks.push(<div key="s2" className="ev spot" title="spot-check ok">•</div>);
        } else {
           blocks.push(<div key="s2" className="ev spot" title="spot-check ok">•</div>);
        }
      } else {
        blocks.push(<div key="s1" className="ev spot" title="spot-check ok">•</div>);
        blocks.push(<div key="l2" className="ev lock" title="locked">…</div>);
        blocks.push(<div key="s2" className="ev spot" title="spot-check ok">•</div>);
        blocks.push(<div key="l3" className="ev lock" title="locked">…</div>);
      }
    }
    
    return <div className="event-strip">{blocks}</div>;
  };

  return (
    <div className="max-w-6xl mx-auto pb-12">
      <div className="flex justify-between items-start mb-6 flex-wrap gap-2.5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1 font-serif">Ingestion Sessions</h1>
          <p className="text-slate-600 text-sm">Streaming connections use sampling + lock instead of matching every event.</p>
        </div>
        <div className="font-mono text-[11px] text-amber-600 border border-brand-amber/35 rounded bg-brand-amber/5 px-2.5 py-1 whitespace-nowrap">
          SANDBOX
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-md">
        <h3 className="m-0 mb-1 text-sm font-bold text-slate-900 flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand-purple" />
          Ingestion Session — streaming
        </h3>
        <p className="m-0 mb-5 text-[13px] text-slate-600"><code className="text-brand-purple font-mono bg-brand-purple/10 px-1 py-0.5 rounded text-[11px]">session_id</code> is attached to every event by the caller; same detect → lock → spot-check lifecycle applies continuously.</p>
        
        {loading ? (
          <p className="text-[13px] text-slate-500 text-center py-6 border border-dashed border-slate-200 rounded-lg">Loading sessions...</p>
        ) : sessions.length === 0 ? (
          <div className="py-10 text-center border border-dashed border-slate-200 rounded-lg">
            <Activity className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-[15px] font-bold text-slate-700">No streaming sessions</h3>
            <p className="text-[13px] text-slate-500 mt-1 max-w-sm mx-auto">Start pushing events with a session_id via the API.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map(session => {
              const total = session.total_events || 0;
              const normalized = session.normalized_count || 0;
              const unresolved = session.unresolved_count || 0;
              return (
              <div className="border border-slate-200 rounded-lg p-4 bg-slate-50" key={session.id}>
                <div className="flex justify-between items-center mb-3 flex-wrap gap-2">
                  <h4 className="m-0 text-[13.5px] font-mono text-brand-purple font-semibold">{session.id} <span className="text-slate-500 font-sans font-normal">— {session.source_id}</span></h4>
                  {session.lock?.status === 'LOCKED' ? (
                    <span className={`inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border ${session.lock.mismatch_count > 0 ? 'bg-brand-amber/10 text-amber-600 border-brand-amber/35' : 'bg-brand-green/10 text-brand-green border-brand-green/35'}`}>
                      locked → {session.lock.rule_name} {session.lock.mismatch_count > 0 ? `(${session.lock.mismatch_count} unresolved)` : ''}
                    </span>
                  ) : (
                    <span className="inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border bg-brand-amber/10 text-amber-600 border-brand-amber/35">
                      status → {session.status}
                    </span>
                  )}
                </div>
                
                <div className="text-[12.5px] text-slate-600 mb-2">
                  Background spot-check runs at ~1-in-500 events even while locked, to catch drift or a multiplexed source.
                </div>
                
                {renderEventStrip(session.lock, true)}
                
                {session.lock?.mismatch_count > 0 && (
                  <div className="text-[12.5px] text-slate-600 mt-2">
                    Event flagged <b className="text-brand-red">unresolved</b> is queued for individual re-matching — the session keeps running, nothing is silently mis-parsed.
                  </div>
                )}

                <div className="flex gap-4 mt-4 mb-2 text-[12px] font-mono text-slate-700">
                  <div className="bg-slate-50 px-3 py-1.5 rounded border border-slate-200">
                    Events: <span className="text-slate-900">{total}</span>
                  </div>
                  <div className="bg-slate-50 px-3 py-1.5 rounded border border-slate-200">
                    Normalized: <span className="text-green-600">{normalized}</span>
                  </div>
                  <div className="bg-slate-50 px-3 py-1.5 rounded border border-slate-200">
                    Unresolved: <span className="text-red-600">{unresolved}</span>
                  </div>
                </div>
                <div className="m-0 text-[12.5px] text-slate-600 font-mono mt-2">
                  Started at: {formatIST(session.started_at)}
                </div>
              </div>
            )})}
          </div>
        )}
      </div>
    </div>
  );
};
