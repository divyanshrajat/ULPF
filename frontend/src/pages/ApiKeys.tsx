import React, { useEffect, useState } from 'react';
import { fetchApiKeys, createApiKey, revokeApiKey } from '../services/api';
import { KeyRound, ShieldAlert } from 'lucide-react';
import { formatIST } from '../utils/date';

export const ApiKeys: React.FC = () => {
  const [keys, setKeys] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKey, setNewKey] = useState<string | null>(null);

  const loadKeys = async () => {
    try {
      const res = await fetchApiKeys();
      setKeys(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadKeys();
  }, []);

  const handleGenerate = async () => {
    try {
      const res = await createApiKey({ name: 'Generated Key', environment: 'production' });
      setNewKey(res.raw_key);
      loadKeys();
    } catch (err) {
      console.error(err);
    }
  };

  const handleRevoke = async (id: string) => {
    try {
      await revokeApiKey(id);
      loadKeys();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="max-w-6xl mx-auto pb-12">
      <div className="flex justify-between items-start mb-6 flex-wrap gap-2.5">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 mb-1 font-serif">API &amp; keys</h1>
          <p className="text-slate-600 text-sm">Keys and endpoints for pushing logs into ULPF.</p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-md mb-6">
        <h3 className="m-0 mb-1 text-sm font-bold text-slate-900 flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-slate-900" />
          API keys
        </h3>
        <p className="m-0 mb-5 text-[13px] text-slate-600">Scoped per source/environment.</p>

        {newKey && (
          <div className="mb-4 p-4 bg-brand-cyan/10 border border-brand-cyan/30 rounded-lg text-slate-900">
            <strong className="font-semibold text-sm">New Key Generated:</strong> <span className="font-mono text-slate-900 text-sm ml-2 bg-black/30 px-2 py-0.5 rounded">{newKey}</span>
            <br/><small className="text-slate-700 mt-1.5 block opacity-80 flex items-center gap-1.5"><ShieldAlert className="w-3.5 h-3.5" /> Please copy this now. You won't be able to see it again.</small>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12.8px] border-collapse mb-4">
            <thead>
              <tr>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Name</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Key</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Scope</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Created</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Status</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Actions</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={6} className="p-8 text-center text-slate-500">Loading API keys...</td></tr>
              ) : keys.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-10 text-center border-b border-slate-200">
                    <KeyRound className="w-8 h-8 text-slate-600 mx-auto mb-2 opacity-50" />
                    <h3 className="text-[14px] font-semibold text-slate-700">No API keys generated</h3>
                    <p className="text-xs text-slate-500 mt-1">Generate a key to start pushing logs to the API.</p>
                  </td>
                </tr>
              ) : (
                keys.map(k => (
                  <tr key={k.id} className="hover:bg-white/5 transition-colors border-b border-slate-200 last:border-0">
                    <td className="py-2.5 px-2.5 font-semibold text-slate-800">{k.name}</td>
                    <td className="py-2.5 px-2.5 font-mono text-slate-900 text-xs">{k.masked_key}</td>
                    <td className="py-2.5 px-2.5 text-slate-600">{k.source_scope}</td>
                    <td className="py-2.5 px-2.5 text-slate-600">{formatIST(k.created_at)}</td>
                    <td className="py-2.5 px-2.5">
                      {k.status === 'active' ? (
                        <span className="inline-block text-[11px] font-mono px-2 py-0.5 rounded-full bg-brand-cyan/10 text-slate-900 border border-brand-cyan/35">active</span>
                      ) : (
                        <span className="inline-block text-[11px] font-mono px-2 py-0.5 rounded-full bg-slate-500/10 text-slate-600 border border-slate-500/35">{k.status}</span>
                      )}
                    </td>
                    <td className="py-2.5 px-2.5">
                      {k.status === 'active' && (
                        <button className="bg-transparent border border-slate-200 text-brand-red font-semibold rounded px-2.5 py-1 text-[11px] hover:bg-brand-red/10 hover:border-brand-red/30 transition-colors" onClick={() => handleRevoke(k.id)}>Revoke</button>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        <div className="flex mt-2">
          <button className="bg-brand-cyan text-white font-bold rounded-lg px-4 py-2 text-[13px] hover:brightness-110 transition-colors" onClick={handleGenerate}>Generate new key</button>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-md">
        <h3 className="m-0 mb-4 text-sm font-bold text-slate-900">Endpoints</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-[12.8px] border-collapse">
            <thead>
              <tr>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Mode</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Endpoint</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Rule selection</th>
                <th className="text-slate-600 font-medium text-[11.5px] uppercase tracking-wide py-2 px-2.5 border-b border-slate-200">Use case</th>
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-slate-200 hover:bg-white/5"><td className="py-2.5 px-2.5 font-semibold text-slate-700">Sync — single event</td><td className="py-2.5 px-2.5 font-mono text-slate-900 text-[12px]">POST /v1/convert</td><td className="py-2.5 px-2.5 font-mono text-slate-600 text-[12px]">rule_id (optional)</td><td className="py-2.5 px-2.5 text-slate-600 text-xs">Low volume/testing; explicit rule_id trusted-but-verified, or auto-detect against Active rules</td></tr>
              <tr className="border-b border-slate-200 hover:bg-white/5"><td className="py-2.5 px-2.5 font-semibold text-slate-700">Batch</td><td className="py-2.5 px-2.5 font-mono text-slate-900 text-[12px]">POST /v1/jobs</td><td className="py-2.5 px-2.5 font-mono text-brand-purple text-[12px]">auto (detect+lock)</td><td className="py-2.5 px-2.5 text-slate-600 text-xs">File upload — detects on first few events, locks, fast-paths the rest</td></tr>
              <tr className="border-b border-slate-200 hover:bg-white/5"><td className="py-2.5 px-2.5 font-semibold text-slate-700">Streaming</td><td className="py-2.5 px-2.5 font-mono text-slate-900 text-[12px]">POST /v1/sessions/{"{"}id{"}"}/events</td><td className="py-2.5 px-2.5 font-mono text-brand-purple text-[12px]">auto (detect+lock)</td><td className="py-2.5 px-2.5 text-slate-600 text-xs">session_id on every event — same detect/lock/spot-check lifecycle</td></tr>
              <tr className="hover:bg-white/5"><td className="py-2.5 px-2.5 font-semibold text-slate-700">UI</td><td className="py-2.5 px-2.5 font-mono text-slate-900 text-[12px]">Upload panel</td><td className="py-2.5 px-2.5 font-mono text-slate-600 text-[12px]">manual</td><td className="py-2.5 px-2.5 text-slate-600 text-xs">One-off conversion, no API key needed</td></tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
