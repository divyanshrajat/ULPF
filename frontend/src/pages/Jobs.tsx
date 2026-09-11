import React, { useEffect, useState } from 'react';
import { fetchJobs } from '../services/api';
import { Layers } from 'lucide-react';
import { formatIST } from '../utils/date';

export const Jobs: React.FC = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const jobsRes = await fetchJobs();
        setJobs(jobsRes.items || []);
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
          <h1 className="text-2xl font-bold text-slate-900 mb-1 font-serif">Ingestion Jobs</h1>
          <p className="text-slate-600 text-sm">Batch uploads use sampling + lock instead of matching every event.</p>
        </div>
        <div className="font-mono text-[11px] text-amber-600 border border-brand-amber/35 rounded bg-brand-amber/5 px-2.5 py-1 whitespace-nowrap">
          SANDBOX
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-md mb-6">
        <h3 className="m-0 mb-1 text-sm font-bold text-slate-900 flex items-center gap-2">
          <Layers className="w-4 h-4 text-slate-900" />
          Ingestion Job — batch upload
        </h3>
        <p className="m-0 mb-5 text-[13px] text-slate-600">First few events are fully matched; once locked, the rest apply the locked rule on the fast path.</p>
        
        {loading ? (
          <p className="text-[13px] text-slate-500 text-center py-6 border border-dashed border-slate-200 rounded-lg">Loading jobs...</p>
        ) : jobs.length === 0 ? (
          <div className="py-10 text-center border border-dashed border-slate-200 rounded-lg">
            <Layers className="w-10 h-10 text-slate-600 mx-auto mb-3" />
            <h3 className="text-[15px] font-bold text-slate-700">No active batch jobs</h3>
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
              <div className="border border-slate-200 rounded-lg p-4 bg-slate-50" key={job.id}>
                <div className="flex justify-between items-center mb-2.5 flex-wrap gap-2">
                  <h4 className="m-0 text-[13.5px] font-mono text-slate-900 font-semibold">{job.id} <span className="text-slate-500 font-sans font-normal">— {job.source_id} {total > 1 ? `(${total.toLocaleString()} events)` : ''}</span></h4>
                  {job.lock?.status === 'LOCKED' ? (
                    <span className="inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border bg-brand-green/10 text-brand-green border-brand-green/35">
                      locked → {job.lock.rule_name}
                    </span>
                  ) : (
                    <span className="inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border bg-brand-amber/10 text-amber-600 border-brand-amber/35">
                      status → {job.status}
                    </span>
                  )}
                </div>
                <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden my-3 relative">
                  <div className="h-full bg-brand-cyan absolute left-0 top-0 transition-all duration-300" style={{ width: `${pct}%` }}></div>
                </div>
                {job.lock?.status === 'LOCKED' && (
                  <div className="text-[12.5px] text-slate-600 mb-2">
                    Detected on events 1–{job.lock.sample_count_seen} (full-field match required on all {job.lock.sample_count_seen}) → locked at event {job.lock.sample_count_seen + 1}. Fast-path applied to remaining {(total - job.lock.sample_count_seen - 1).toLocaleString()} events.
                  </div>
                )}
                {job.lock?.status === 'SAMPLING' && (
                  <div className="text-[12.5px] text-slate-600 mb-2">
                    Detecting rules on initial samples ({job.lock.sample_count_seen}/3 seen)...
                  </div>
                )}
                {renderEventStrip(job.lock, false)}
                
                <div className="flex justify-between text-[11px] text-slate-600 font-mono mt-4 mb-2">
                  <span>{pct}% ({processed}/{total})</span>
                  <span><span className="text-green-400">{normalized} norm</span> | <span className="text-red-400">{unresolved} unres</span></span>
                </div>
                <div className="m-0 text-[12.5px] text-slate-600 font-mono">
                  Started at: {formatIST(job.started_at)}
                </div>
              </div>
            )})}
          </div>
        )}
      </div>

    </div>
  );
};
