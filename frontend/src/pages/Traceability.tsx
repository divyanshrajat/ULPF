import { useState } from 'react';
import { API_BASE } from '../services/api';

export function Traceability() {
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
          className="px-5 py-2 bg-white hover:bg-slate-100 text-slate-950 rounded-md font-bold shadow-md shadow-white/10 transition-all"
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
  );
}
