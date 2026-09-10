import React, { useEffect, useState } from 'react';
import { fetchJobs, fetchSessions } from '../services/api';
import { Layers, Activity } from 'lucide-react';
import { formatIST } from '../utils/date';

export const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [jobsRes, sessionsRes] = await Promise.all([
          fetchJobs(),
          fetchSessions()
        ]);
        setJobs(jobsRes.items || []);
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
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Jobs &amp; sessions</h1>
          <p className="text-slate-400 text-sm">Batch uploads and streaming connections use sampling + lock instead of matching every event.</p>
        </div>
        <div className="font-mono text-[11px] text-brand-amber border border-brand-amber/35 rounded bg-brand-amber/5 px-2.5 py-1 whitespace-nowrap">
          SANDBOX
        </div>
      </div>

      <div className="bg-[#101D24] border border-[#1E3038] rounded-xl p-6 shadow-md mb-6">
        <h3 className="m-0 mb-1 text-sm font-bold text-slate-100 flex items-center gap-2">
          <Layers className="w-4 h-4 text-brand-cyan" />
          Ingestion Job — batch upload
        </h3>
        <p className="m-0 mb-5 text-[13px] text-slate-400">First few events are fully matched; once locked, the rest apply the locked rule on the fast path.</p>
        
        {loading ? (
          <p className="text-[13px] text-slate-500 text-center py-6 border border-dashed border-[#1E3038] rounded-lg">Loading jobs...</p>
        ) : jobs.length === 0 ? (
          <div className="py-10 text-center border border-dashed border-[#1E3038] rounded-lg">
            <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-[15px] font-bold text-slate-300">No active batch jobs</h3>
            <p className="text-[13px] text-slate-500 mt-1 max-w-sm mx-auto">Upload a batch file via the API to see it tracked here.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {jobs.map(job => {
              const total = job.total_events || 1;
              const processed = job.processed_events || 0;
              const normalized = job.normalized_count || 0;
              const unresolved = job.unresolved_count || 0;
              const pct = job.status === "COMPLETED" ? 100 : Math.round((processed / total) * 100);
              
              return (
              <div className="border border-[#1E3038] rounded-lg p-4 bg-[#0D1920]" key={job.id}>
                <div className="flex justify-between items-center mb-2.5 flex-wrap gap-2">
                  <h4 className="m-0 text-[13.5px] font-mono text-brand-cyan font-semibold">{job.id} <span className="text-slate-500 font-sans font-normal">— {job.source_id} {total > 1 ? `(${total.toLocaleString()} events)` : ''}</span></h4>
                  {job.lock?.status === 'LOCKED' ? (
                    <span className="inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border bg-brand-green/10 text-brand-green border-brand-green/35">
                      locked → {job.lock.rule_name}
                    </span>
                  ) : (
                    <span className="inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border bg-brand-amber/10 text-brand-amber border-brand-amber/35">
                      status → {job.status}
                    </span>
                  )}
                </div>
                <div className="h-1.5 bg-[#1E3038] rounded-full overflow-hidden my-3 relative">
                  <div className="h-full bg-brand-cyan absolute left-0 top-0 transition-all duration-300" style={{ width: `${pct}%` }}></div>
                </div>
                {job.lock?.status === 'LOCKED' && (
                  <div className="text-[12.5px] text-slate-400 mb-2">
                    Detected on events 1–{job.lock.sample_count_seen} (full-field match required on all {job.lock.sample_count_seen}) → locked at event {job.lock.sample_count_seen + 1}. Fast-path applied to remaining {(total - job.lock.sample_count_seen - 1).toLocaleString()} events.
                  </div>
                )}
                {job.lock?.status === 'SAMPLING' && (
                  <div className="text-[12.5px] text-slate-400 mb-2">
                    Detecting rules on initial samples ({job.lock.sample_count_seen}/3 seen)...
                  </div>
                )}
                {renderEventStrip(job.lock, false)}
                
                <div className="flex justify-between text-[11px] text-slate-400 font-mono mt-4 mb-2">
                  <span>{pct}% ({processed}/{total})</span>
                  <span><span className="text-green-400">{normalized} norm</span> | <span className="text-red-400">{unresolved} unres</span></span>
                </div>
                <div className="m-0 text-[12.5px] text-slate-400 font-mono">
                  Started at: {formatIST(job.started_at)}
                </div>
              </div>
            )})}
          </div>
        )}
      </div>

      <div className="bg-[#101D24] border border-[#1E3038] rounded-xl p-6 shadow-md">
        <h3 className="m-0 mb-1 text-sm font-bold text-slate-100 flex items-center gap-2">
          <Activity className="w-4 h-4 text-brand-purple" />
          Ingestion Session — streaming
        </h3>
        <p className="m-0 mb-5 text-[13px] text-slate-400"><code className="text-brand-purple font-mono bg-brand-purple/10 px-1 py-0.5 rounded text-[11px]">session_id</code> is attached to every event by the caller; same detect → lock → spot-check lifecycle applies continuously.</p>
        
        {loading ? (
          <p className="text-[13px] text-slate-500 text-center py-6 border border-dashed border-[#1E3038] rounded-lg">Loading sessions...</p>
        ) : sessions.length === 0 ? (
          <div className="py-10 text-center border border-dashed border-[#1E3038] rounded-lg">
            <Activity className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-[15px] font-bold text-slate-300">No streaming sessions</h3>
            <p className="text-[13px] text-slate-500 mt-1 max-w-sm mx-auto">Start pushing events with a session_id via the API.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {sessions.map(session => {
              const total = session.total_events || 0;
              const normalized = session.normalized_count || 0;
              const unresolved = session.unresolved_count || 0;
              return (
              <div className="border border-[#1E3038] rounded-lg p-4 bg-[#0D1920]" key={session.id}>
                <div className="flex justify-between items-center mb-3 flex-wrap gap-2">
                  <h4 className="m-0 text-[13.5px] font-mono text-brand-purple font-semibold">{session.id} <span className="text-slate-500 font-sans font-normal">— {session.source_id}</span></h4>
                  {session.lock?.status === 'LOCKED' ? (
                    <span className={`inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border ${session.lock.mismatch_count > 0 ? 'bg-brand-amber/10 text-brand-amber border-brand-amber/35' : 'bg-brand-green/10 text-brand-green border-brand-green/35'}`}>
                      locked → {session.lock.rule_name} {session.lock.mismatch_count > 0 ? `(${session.lock.mismatch_count} unresolved)` : ''}
                    </span>
                  ) : (
                    <span className="inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border bg-brand-amber/10 text-brand-amber border-brand-amber/35">
                      status → {session.status}
                    </span>
                  )}
                </div>
                
                <div className="text-[12.5px] text-slate-400 mb-2">
                  Background spot-check runs at ~1-in-500 events even while locked, to catch drift or a multiplexed source.
                </div>
                
                {renderEventStrip(session.lock, true)}
                
                {session.lock?.mismatch_count > 0 && (
                  <div className="text-[12.5px] text-slate-400 mt-2">
                    Event flagged <b className="text-brand-red">unresolved</b> is queued for individual re-matching — the session keeps running, nothing is silently mis-parsed.
                  </div>
                )}

                <div className="flex gap-4 mt-4 mb-2 text-[12px] font-mono text-slate-300">
                  <div className="bg-[#16252D] px-3 py-1.5 rounded border border-[#1E3038]">
                    Events: <span className="text-white">{total}</span>
                  </div>
                  <div className="bg-[#16252D] px-3 py-1.5 rounded border border-[#1E3038]">
                    Normalized: <span className="text-green-400">{normalized}</span>
                  </div>
                  <div className="bg-[#16252D] px-3 py-1.5 rounded border border-[#1E3038]">
                    Unresolved: <span className="text-red-400">{unresolved}</span>
                  </div>
                </div>
                <div className="m-0 text-[12.5px] text-slate-400 font-mono mt-2">
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
