import React, { useEffect, useState } from 'react';
import { fetchApiKeys, createApiKey, revokeApiKey } from '../services/api';

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
    <div className="view active">
      <div className="topbar">
        <div>
          <h1>API &amp; keys</h1>
          <p>Keys and endpoints for pushing logs into ULPF.</p>
        </div>
        <div className="env-badge">SANDBOX</div>
      </div>

      <div className="panel">
        <h3>API keys</h3>
        <p className="hint">Scoped per source/environment.</p>

        {newKey && (
          <div style={{ marginBottom: '16px', padding: '12px', background: 'rgba(63,208,201,0.1)', border: '1px solid var(--cyan)', borderRadius: '4px', color: 'var(--cyan)' }}>
            <strong>New Key Generated:</strong> <span className="mono">{newKey}</span>
            <br/><small>Please copy this now. You won't be able to see it again.</small>
          </div>
        )}

        <table>
          <thead>
            <tr>
              <th>Name</th>
              <th>Key</th>
              <th>Scope</th>
              <th>Created</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6}>Loading...</td></tr>
            ) : keys.length === 0 ? (
              <tr><td colSpan={6}>No API keys found.</td></tr>
            ) : (
              keys.map(k => (
                <tr key={k.id}>
                  <td>{k.name}</td>
                  <td className="mono">{k.masked_key}</td>
                  <td>{k.source_scope}</td>
                  <td>{new Date(k.created_at).toISOString().split('T')[0]}</td>
                  <td>
                    {k.status === 'active' ? (
                      <span className="badge ok">active</span>
                    ) : (
                      <span className="badge dim">{k.status}</span>
                    )}
                  </td>
                  <td>
                    {k.status === 'active' && (
                      <button className="btn btn-ghost" style={{ padding: '4px 8px', fontSize: '11px' }} onClick={() => handleRevoke(k.id)}>Revoke</button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
        <div className="btn-row" style={{ marginTop: '14px' }}>
          <button className="btn btn-primary" onClick={handleGenerate}>Generate new key</button>
        </div>
      </div>

      <div className="panel">
        <h3>Endpoints</h3>
        <table>
          <thead>
            <tr>
              <th>Mode</th>
              <th>Endpoint</th>
              <th>Rule selection</th>
              <th>Use case</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>Sync — single event</td><td className="mono">POST /v1/convert</td><td className="mono">rule_id (optional)</td><td>Low volume/testing; explicit rule_id trusted-but-verified, or auto-detect against Active rules</td></tr>
            <tr><td>Batch</td><td className="mono">POST /v1/jobs</td><td className="mono">auto (detect+lock)</td><td>File upload — detects on first few events, locks, fast-paths the rest</td></tr>
            <tr><td>Streaming</td><td className="mono">POST /v1/sessions/{"{"}id{"}"}/events</td><td className="mono">auto (detect+lock)</td><td>session_id on every event — same detect/lock/spot-check lifecycle</td></tr>
            <tr><td>UI</td><td className="mono">Upload panel</td><td className="mono">manual</td><td>One-off conversion, no API key needed</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  );
};
