import React, { useEffect, useState, useRef } from 'react';
import { fetchSessions, fetchSources, createSession, submitSessionEvents } from '../services/api';
import { Activity, Play, Square, Send } from 'lucide-react';
import { formatIST } from '../utils/date';

export const Sessions: React.FC = () => {
  const [sessions, setSessions] = useState<any[]>([]);
  const [sources, setSources] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedSource, setSelectedSource] = useState<string>('');
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [startingSession, setStartingSession] = useState(false);
  
  const [manualText, setManualText] = useState('');
  const [sendingManual, setSendingManual] = useState(false);
  
  const [replayFile, setReplayFile] = useState<File | null>(null);
  const [replayActive, setReplayActive] = useState(false);
  const replayIntervalRef = useRef<number | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = async () => {
    try {
      const [sessionsRes, sourcesRes] = await Promise.all([
        fetchSessions(),
        fetchSources()
      ]);
      setSessions(sessionsRes.items || []);
      setSources(sourcesRes || []);
      if (sourcesRes && sourcesRes.length > 0 && !selectedSource) {
        setSelectedSource(sourcesRes[0].source_id);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    return () => stopReplay();
  }, []);

  const handleStartSession = async () => {
    if (!selectedSource) return;
    setStartingSession(true);
    try {
      const res = await createSession(selectedSource);
      setActiveSessionId(res.session_id);
      await loadData();
    } catch (err) {
      console.error("Failed to start session:", err);
      alert("Failed to start session. Check console.");
    } finally {
      setStartingSession(false);
    }
  };

  const handleSendManual = async () => {
    if (!activeSessionId || !manualText.trim()) return;
    setSendingManual(true);
    try {
      const events = manualText.split('\n').filter(l => l.trim().length > 0);
      if (events.length > 0) {
        await submitSessionEvents(activeSessionId, events);
        setManualText('');
        await loadData();
      }
    } catch (err) {
      console.error("Failed to submit manual events:", err);
      alert("Failed to send events.");
    } finally {
      setSendingManual(false);
    }
  };

  const stopReplay = () => {
    if (replayIntervalRef.current !== null) {
      window.clearInterval(replayIntervalRef.current);
      replayIntervalRef.current = null;
    }
    setReplayActive(false);
  };

  const handleStartReplay = () => {
    if (!activeSessionId || !replayFile) return;
    setReplayActive(true);

    const reader = new FileReader();
    reader.onload = async (e) => {
      const text = e.target?.result as string;
      if (!text) {
        stopReplay();
        return;
      }
      
      const lines = text.split('\n').filter(l => l.trim().length > 0);
      let index = 0;
      
      replayIntervalRef.current = window.setInterval(async () => {
        if (index >= lines.length) {
          stopReplay();
          return;
        }
        
        // Take 2-3 lines at a time
        const batchSize = Math.floor(Math.random() * 2) + 2;
        const batch = lines.slice(index, index + batchSize);
        index += batchSize;
        
        if (batch.length > 0) {
          try {
            await submitSessionEvents(activeSessionId, batch);
            await loadData(); // refresh UI automatically
          } catch (err) {
            console.error("Auto-replay failed:", err);
            stopReplay();
          }
        }
      }, 800);
    };
    reader.onerror = () => {
      console.error("Failed to read file.");
      stopReplay();
    };
    reader.readAsText(replayFile);
  };

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

      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm mb-6">
        {!activeSessionId ? (
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1 w-full">
              <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Target Source</label>
              <select 
                value={selectedSource}
                onChange={e => setSelectedSource(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-lg text-slate-800 px-3 py-2 text-[13px] outline-none focus:border-brand-purple/50"
              >
                {sources.map(s => (
                  <option key={s.source_id} value={s.source_id}>{s.name}</option>
                ))}
              </select>
            </div>
            <div className="w-full md:w-auto">
              <button 
                disabled={!selectedSource || startingSession}
                onClick={handleStartSession}
                className="w-full md:w-auto bg-brand-purple text-white font-bold rounded-lg px-4 py-2 text-[13px] hover:brightness-110 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {startingSession ? <Activity className="w-4 h-4 animate-pulse" /> : <Play className="w-4 h-4 fill-current" />}
                Start session
              </button>
            </div>
          </div>
        ) : (
          <div>
            <div className="flex justify-between items-center mb-4 pb-4 border-b border-slate-100">
              <h3 className="text-[14px] font-bold text-slate-800 flex items-center gap-2">
                <Activity className="w-4 h-4 text-brand-purple" /> Active Session: <span className="font-mono font-normal text-brand-purple bg-brand-purple/10 px-1.5 py-0.5 rounded">{activeSessionId}</span>
              </h3>
              <button onClick={() => { stopReplay(); setActiveSessionId(''); }} className="text-xs text-slate-500 hover:text-slate-800 underline">Close & Start New</button>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Manual Feed (Paste Logs)</label>
                <textarea 
                  value={manualText}
                  onChange={e => setManualText(e.target.value)}
                  placeholder="Paste log lines here (one per line)..."
                  className="w-full h-32 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 px-3 py-2 text-[13px] font-mono outline-none focus:border-brand-purple/50 resize-none mb-3"
                />
                <button 
                  onClick={handleSendManual}
                  disabled={!manualText.trim() || sendingManual || replayActive}
                  className="bg-slate-800 text-white font-bold rounded-lg px-4 py-2 text-[13px] hover:bg-slate-700 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Send className="w-4 h-4" /> Send manual events
                </button>
              </div>
              
              <div>
                <label className="block text-xs font-semibold text-slate-600 uppercase tracking-wider mb-2">Auto-Replay from File</label>
                <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 flex flex-col justify-center min-h-[128px]">
                  <input 
                    type="file" 
                    ref={fileInputRef}
                    disabled={replayActive}
                    onChange={e => setReplayFile(e.target.files ? e.target.files[0] : null)}
                    className="block w-full text-[13px] text-slate-600 file:mr-4 file:py-1.5 file:px-3 file:rounded file:border-0 file:text-[13px] file:font-semibold file:bg-slate-200 file:text-slate-800 hover:file:bg-slate-300 focus:outline-none mb-4 disabled:opacity-50"
                  />
                  
                  {replayActive ? (
                    <button 
                      onClick={stopReplay}
                      className="w-full bg-red-500 text-white font-bold rounded-lg px-4 py-2 text-[13px] hover:bg-red-600 transition-colors shadow-sm flex items-center justify-center gap-2"
                    >
                      <Square className="w-4 h-4 fill-current" /> Stop replay
                    </button>
                  ) : (
                    <button 
                      disabled={!replayFile}
                      onClick={handleStartReplay}
                      className="w-full bg-brand-purple text-white font-bold rounded-lg px-4 py-2 text-[13px] hover:brightness-110 transition-colors shadow-sm disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                    >
                      <Play className="w-4 h-4 fill-current" /> Auto-replay (2-3 lines/sec)
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
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
