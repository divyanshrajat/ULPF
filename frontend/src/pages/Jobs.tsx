import React, { useEffect, useState } from 'react';
import { fetchJobs, fetchSessions } from '../services/api';
import { Layers, Activity } from 'lucide-react';

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
            {jobs.map(job => (
              <div className="border border-[#1E3038] rounded-lg p-4 bg-[#0D1920]" key={job.id}>
                <div className="flex justify-between items-center mb-2.5 flex-wrap gap-2">
                  <h4 className="m-0 text-[13.5px] font-mono text-brand-cyan font-semibold">{job.id} <span className="text-slate-500 font-sans font-normal">— {job.source_id}</span></h4>
                  <span className="inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border bg-brand-green/10 text-brand-green border-brand-green/35">status → {job.status}</span>
                </div>
                <div className="h-1.5 bg-[#1E3038] rounded-full overflow-hidden my-3">
                  <div className="h-full bg-brand-cyan w-full"></div>
                </div>
                <div className="m-0 text-[12.5px] text-slate-400 font-mono">
                  Started at: {new Date(job.started_at).toLocaleString()}
                </div>
              </div>
            ))}
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
            {sessions.map(session => (
              <div className="border border-[#1E3038] rounded-lg p-4 bg-[#0D1920]" key={session.id}>
                <div className="flex justify-between items-center mb-2 flex-wrap gap-2">
                  <h4 className="m-0 text-[13.5px] font-mono text-brand-purple font-semibold">{session.id} <span className="text-slate-500 font-sans font-normal">— {session.source_id}</span></h4>
                  <span className="inline-block text-[11px] font-mono px-2.5 py-0.5 rounded-full border bg-brand-amber/10 text-brand-amber border-brand-amber/35">status → {session.status}</span>
                </div>
                <div className="m-0 text-[12.5px] text-slate-400 font-mono mt-2">
                  Started at: {new Date(session.started_at).toLocaleString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
