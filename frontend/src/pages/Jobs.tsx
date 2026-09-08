import React, { useEffect, useState } from 'react';
import { fetchJobs, fetchSessions } from '../services/api';

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
    <div className="view active">
      <div className="topbar">
        <div>
          <h1>Jobs &amp; sessions</h1>
          <p>Batch uploads and streaming connections use sampling + lock instead of matching every event.</p>
        </div>
        <div className="env-badge">SANDBOX</div>
      </div>

      <div className="panel">
        <h3>Ingestion Job — batch upload</h3>
        <p className="hint">First few events are fully matched; once locked, the rest apply the locked rule on the fast path.</p>
        
        {loading ? (
          <p className="hint">Loading jobs...</p>
        ) : jobs.length === 0 ? (
          <p className="hint">No batch jobs found.</p>
        ) : (
          jobs.map(job => (
            <div className="job-card" key={job.id}>
              <div className="job-head">
                <h4 className="mono">{job.id} — {job.source_id}</h4>
                <span className="badge ok">status → {job.status}</span>
              </div>
              <div className="progress-track">
                <div className="progress-fill" style={{ width: '100%' }}></div>
              </div>
              <div className="hint" style={{ margin: 0 }}>
                Started at: {new Date(job.started_at).toLocaleString()}
              </div>
            </div>
          ))
        )}

        <h3 style={{ marginTop: '22px' }}>Ingestion Session — streaming</h3>
        <p className="hint">session_id is attached to every event by the caller; same detect → lock → spot-check lifecycle applies continuously.</p>
        
        {loading ? (
          <p className="hint">Loading sessions...</p>
        ) : sessions.length === 0 ? (
          <p className="hint">No streaming sessions found.</p>
        ) : (
          sessions.map(session => (
            <div className="job-card" key={session.id}>
              <div className="job-head">
                <h4 className="mono">{session.id} — {session.source_id}</h4>
                <span className="badge warn">status → {session.status}</span>
              </div>
              <div className="hint" style={{ margin: '0 0 8px' }}>
                Started at: {new Date(session.started_at).toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
