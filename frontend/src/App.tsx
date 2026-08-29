import { useState, useEffect } from 'react'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <div className="flex h-screen bg-slate-900 text-slate-300 font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-850 border-r border-slate-800 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-800">
          <h1 className="text-xl font-bold text-cyan-400 tracking-wider">ULPF</h1>
        </div>
        <nav className="flex-1 py-4">
          <ul className="space-y-1 px-3">
            {[
              { id: 'dashboard', label: 'Dashboard' },
              { id: 'onboarding', label: 'Onboarding' },
              { id: 'review', label: 'Review Queue' },
              { id: 'events', label: 'Events' },
              { id: 'traceability', label: 'Traceability' },
            ].map((tab) => (
              <li key={tab.id}>
                <button
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full text-left px-3 py-2 rounded-md transition-colors ${
                    activeTab === tab.id ? 'bg-slate-800 text-cyan-400' : 'hover:bg-slate-800 hover:text-white'
                  }`}
                >
                  {tab.label}
                </button>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        <header className="h-16 bg-slate-850 border-b border-slate-800 flex items-center px-6">
          <h2 className="text-lg font-medium text-slate-200 capitalize">{activeTab.replace('-', ' ')}</h2>
        </header>
        
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'dashboard' && <Dashboard />}
          {activeTab === 'onboarding' && <Onboarding />}
          {activeTab === 'review' && <ReviewQueue />}
          {activeTab === 'events' && <Events />}
          {activeTab === 'traceability' && <Traceability />}
        </div>
      </main>
    </div>
  )
}

function Dashboard() {
  const [stats, setStats] = useState({ events_ingested: 0, events_normalized: 0, review_queue: 0, dead_letters: 0 });

  useEffect(() => {
    fetch(`${API_BASE}/stats`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        <StatCard title="Events Ingested" value={stats.events_ingested.toString()} />
        <StatCard title="Events Normalized" value={stats.events_normalized.toString()} />
        <StatCard title="Review Queue" value={stats.review_queue.toString()} alert={stats.review_queue > 0} />
        <StatCard title="Dead Letters" value={stats.dead_letters.toString()} success={stats.dead_letters === 0} alert={stats.dead_letters > 0} />
      </div>
    </div>
  )
}

function StatCard({ title, value, alert, success }: { title: string, value: string, alert?: boolean, success?: boolean }) {
  let color = "text-slate-200";
  if (alert) color = "text-amber-400";
  if (success) color = "text-green-400";
  
  return (
    <div className="bg-slate-850 border border-slate-800 rounded-lg p-4">
      <h3 className="text-sm text-slate-400 uppercase tracking-wider mb-2">{title}</h3>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  )
}

function Onboarding() {
  const [step, setStep] = useState(1);
  const [sampleLog, setSampleLog] = useState("");
  const [sourceId, setSourceId] = useState("FW-X");
  const [proposals, setProposals] = useState<any[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [pattern, setPattern] = useState("");

  const handleAnalyze = async () => {
    try {
      const res = await fetch(`${API_BASE}/onboarding/sample`, {
        method: 'POST',
        headers: { 'X-ULPF-Source-ID': sourceId, 'Content-Type': 'text/plain' },
        body: sampleLog
      });
      const data = await res.json();
      if (res.ok) {
        setProposals(data.proposals);
        setTemplateId(data.template_id);
        setPattern(data.pattern);
        setStep(2);
      } else {
        alert(data.detail || "Analysis failed");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleApprove = async () => {
    try {
      const res = await fetch(`${API_BASE}/mappings/${sourceId}/${templateId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ field_bindings: {}, confidence_summary: {} })
      });
      if (res.ok) {
        alert("Mapping approved successfully!");
        setStep(1);
        setSampleLog("");
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-slate-850 border border-slate-800 rounded-lg p-6">
        <h3 className="text-lg font-medium text-white mb-4">Onboard New Source</h3>
        {step === 1 && (
          <div className="space-y-4">
            <p className="text-sm text-slate-400">Provide a Source ID and sample log line to begin structure discovery.</p>
            <input 
              type="text" 
              value={sourceId} 
              onChange={e => setSourceId(e.target.value)} 
              placeholder="Source ID"
              className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-white"
            />
            <textarea 
              value={sampleLog}
              onChange={e => setSampleLog(e.target.value)}
              className="w-full h-32 bg-slate-900 border border-slate-700 rounded p-2 text-white font-mono text-sm"
              placeholder="Paste raw log event here..."
            />
            <button 
              onClick={handleAnalyze}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-sm font-medium transition-colors"
            >
              Analyze Sample
            </button>
          </div>
        )}
        {step === 2 && (
          <div className="space-y-4">
            <div className="p-4 bg-slate-900 rounded border border-slate-800">
              <p className="text-xs text-slate-400 mb-2">Discovered Pattern</p>
              <p className="font-mono text-sm text-cyan-400 bg-slate-950 p-2 rounded">
                {pattern}
              </p>
            </div>
            
            <div className="mt-4">
              <h4 className="text-sm font-medium mb-2">Proposals</h4>
              <div className="bg-slate-950 p-4 rounded max-h-64 overflow-y-auto">
                {proposals.map((p, idx) => (
                  <div key={idx} className="flex justify-between items-center border-b border-slate-800 py-2">
                    <span className="font-mono text-xs text-slate-400">{p.source_field}</span>
                    <span className="text-xs text-slate-500">→</span>
                    <span className="font-mono text-xs text-cyan-400">{p.proposed_target}</span>
                    <span className="text-xs bg-slate-800 px-2 rounded">Conf: {p.confidence.toFixed(2)}</span>
                  </div>
                ))}
              </div>
            </div>

            <button 
              onClick={handleApprove}
              className="px-4 py-2 bg-green-600 hover:bg-green-500 text-white rounded text-sm font-medium transition-colors"
            >
              Approve Mapping
            </button>
            <button 
              onClick={() => setStep(1)}
              className="px-4 py-2 ml-2 bg-slate-600 hover:bg-slate-500 text-white rounded text-sm font-medium transition-colors"
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

function ReviewQueue() {
  const [queue, setQueue] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/review/queue`)
      .then(res => res.json())
      .then(data => setQueue(data))
      .catch(console.error);
  }, []);

  return (
    <div className="bg-slate-850 border border-slate-800 rounded-lg overflow-hidden">
      <table className="w-full text-left text-sm">
        <thead className="bg-slate-900 border-b border-slate-800 text-slate-400">
          <tr>
            <th className="p-4 font-medium">Source</th>
            <th className="p-4 font-medium">Template ID</th>
            <th className="p-4 font-medium">Mapping ID</th>
            <th className="p-4 font-medium">Confidence</th>
            <th className="p-4 font-medium">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-800">
          {queue.length === 0 && (
            <tr><td colSpan={5} className="p-4 text-center text-slate-500">No pending reviews</td></tr>
          )}
          {queue.map((item, idx) => (
            <tr key={idx} className="hover:bg-slate-800/50">
              <td className="p-4 text-slate-300">{item.source_id}</td>
              <td className="p-4 font-mono text-cyan-400">{item.template_id}</td>
              <td className="p-4 font-mono text-amber-400">{item.mapping_id}</td>
              <td className="p-4"><span className="text-amber-400 font-medium">{item.confidence}</span></td>
              <td className="p-4">
                <button className="text-xs px-3 py-1 bg-slate-700 hover:bg-slate-600 rounded">Review</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function Events() {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/events`)
      .then(res => res.json())
      .then(data => {
        setEvents(Array.isArray(data) ? data : []);
        setLoading(false);
      })
      .catch(e => {
        console.error(e);
        setLoading(false);
      });
  }, []);

  return (
    <div className="bg-slate-850 border border-slate-800 rounded-lg overflow-hidden p-4">
      {loading ? <p className="text-slate-400">Loading events...</p> : (
        <div className="space-y-2">
          {events.length === 0 && <p className="text-slate-500">No events indexed in OpenSearch yet.</p>}
          {events.map((ev, idx) => (
            <div key={idx} className="p-3 bg-slate-900 border border-slate-800 rounded">
              <div className="flex justify-between items-center mb-2">
                <span className="text-xs text-slate-500 font-mono">{ev.trace_id}</span>
                <span className="text-xs text-slate-400">{ev['@timestamp']}</span>
              </div>
              <pre className="text-xs text-cyan-400 font-mono overflow-x-auto">
                {JSON.stringify(ev, null, 2)}
              </pre>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function Traceability() {
  const [traceId, setTraceId] = useState("");
  const [raw, setRaw] = useState<any>(null);
  const [prov, setProv] = useState<any[]>([]);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!traceId) return;
    setSearched(true);
    try {
      const resRaw = await fetch(`${API_BASE}/events/${traceId}/raw`);
      const dataRaw = await resRaw.json();
      setRaw(dataRaw.error ? null : dataRaw);

      const resProv = await fetch(`${API_BASE}/events/${traceId}/provenance`);
      const dataProv = await resProv.json();
      setProv(Array.isArray(dataProv) ? dataProv : []);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex space-x-2 mb-6">
        <input 
          type="text" 
          value={traceId}
          onChange={e => setTraceId(e.target.value)}
          placeholder="Enter Trace ID..."
          className="flex-1 bg-slate-900 border border-slate-700 rounded p-2 text-white font-mono"
        />
        <button 
          onClick={handleSearch}
          className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-medium transition-colors"
        >
          Trace
        </button>
      </div>

      {searched && !raw && <p className="text-amber-400">Event not found in raw vault.</p>}

      {raw && (
        <div className="flex space-x-4">
          <div className="flex-1 bg-slate-850 p-4 border border-slate-800 rounded-lg">
            <h3 className="text-sm font-medium text-slate-400 mb-2">RAW EVENT VAULT</h3>
            <pre className="text-xs text-slate-300 bg-slate-950 p-3 rounded font-mono overflow-x-auto whitespace-pre-wrap">
              {raw.payload}
            </pre>
            <div className="mt-3 flex items-center space-x-2 text-xs">
              {raw.verified ? 
                <span className="text-green-400 font-medium">✓ SHA-256 VERIFIED</span> :
                <span className="text-red-400 font-medium">✗ DIGEST MISMATCH</span>
              }
              <span className="text-slate-500 font-mono truncate max-w-xs" title={raw.digest}>{raw.digest}</span>
            </div>
          </div>
          
          <div className="flex-1 bg-slate-850 p-4 border border-slate-800 rounded-lg">
            <h3 className="text-sm font-medium text-slate-400 mb-2">PROVENANCE CHAIN</h3>
            {prov.length === 0 ? <p className="text-xs text-slate-500">No provenance records found.</p> : (
              <div className="space-y-2 max-h-96 overflow-y-auto pr-2">
                {prov.map((p, idx) => (
                  <div key={idx} className="text-xs p-2 bg-slate-950 rounded border border-slate-800">
                    <div className="flex justify-between text-slate-500 mb-1">
                      <span>{p.transformation}</span>
                      <span>Conf: {p.confidence?.toFixed(2) || 'N/A'}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-slate-400 font-mono">{p.source_field}</span>
                      <span className="text-slate-500">→</span>
                      <span className="text-cyan-400 font-mono">{p.target_field}</span>
                    </div>
                    <div className="mt-1 text-slate-500 truncate">Value: {p.source_value}</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default App
