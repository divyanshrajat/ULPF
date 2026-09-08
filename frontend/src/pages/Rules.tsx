import React, { useEffect, useState } from 'react';
import { fetchRules, updateRuleLifecycle } from '../services/api';

export const Rules: React.FC = () => {
  const [rules, setRules] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadRules = async () => {
    try {
      const data = await fetchRules();
      setRules(Array.isArray(data) ? data : (data as any).items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRules();
  }, []);

  const changeState = async (ruleId: string, newState: string) => {
    try {
      if (newState === 'Active') {
        await updateRuleLifecycle(ruleId, { action: 'approve' });
      } else if (newState === 'Disabled') {
        await updateRuleLifecycle(ruleId, { action: 'reject' });
      }
      loadRules();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="view active">
      <div className="topbar">
        <div>
          <h1>Rule registry</h1>
          <p>Every rule your team has authored, versioned and lifecycle-managed.</p>
        </div>
        <div className="env-badge">SANDBOX</div>
      </div>
      <div className="panel">
        <div className="lifecycle-legend">
          <span><b>Active</b> — auto-detect + explicit calls</span>
          <span><b>Deprecated</b> — explicit calls only</span>
          <span><b>Disabled</b> — rejected even if called</span>
          <span><b>Archived</b> — history only, not invokable</span>
        </div>
        <table>
          <thead>
            <tr>
              <th>Rule ID</th>
              <th>Schema</th>
              <th>Status</th>
              <th>Updated</th>
              <th>State</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={5}>Loading...</td></tr>
            ) : rules.length === 0 ? (
              <tr><td colSpan={5}>No rules found.</td></tr>
            ) : (
              rules.map((f) => {
                const uiState = f.status === 'ACTIVE' ? 'Active' : f.status === 'REJECTED' ? 'Disabled' : 'Archived';
                
                return (
                  <tr key={f.id}>
                    <td className="mono">{f.name}@{f.version}</td>
                    <td>{f.target_schema}</td>
                    <td>{f.status}</td>
                    <td>{new Date(f.updated_at).toISOString().split('T')[0]}</td>
                    <td>
                      <select 
                        className="state-select" 
                        value={uiState}
                        onChange={(e) => changeState(f.id, e.target.value)}
                      >
                        <option value="Active">Active</option>
                        <option value="Deprecated">Deprecated</option>
                        <option value="Disabled">Disabled</option>
                        <option value="Archived">Archived</option>
                      </select>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
