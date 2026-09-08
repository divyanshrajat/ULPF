import React, { useEffect, useState } from 'react';
import { fetchEvents } from '../services/api';

export const Events: React.FC = () => {
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [masked, setMasked] = useState(true);
  const [openDetail, setOpenDetail] = useState<number | null>(null);

  useEffect(() => {
    const loadEvents = async () => {
      try {
        const data = await fetchEvents({ page_size: 50 });
        setEvents(data.items || []);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    loadEvents();
  }, []);

  const toggleDetail = (index: number) => {
    setOpenDetail(openDetail === index ? null : index);
  };

  return (
    <div className="view active">
      <div className="topbar">
        <div>
          <h1>Log review</h1>
          <p>Every raw event, its normalized output, and the exact rule used.</p>
        </div>
        <div className="env-badge">SANDBOX</div>
      </div>

      <div className="panel">
        <div className="toolbar">
          <div className="hint" style={{ margin: 0 }}>Click a row to inspect raw vs. normalized.</div>
          <label className="switch">
            <input type="checkbox" checked={masked} onChange={(e) => setMasked(e.target.checked)} />
            Mask sensitive fields
          </label>
        </div>
        <table>
          <thead>
            <tr>
              <th></th>
              <th>Timestamp</th>
              <th>Source</th>
              <th>Rule used</th>
              <th>Status</th>
              <th>Trace UUID</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={6}>Loading...</td></tr>
            ) : events.length === 0 ? (
              <tr><td colSpan={6}>No events found.</td></tr>
            ) : (
              events.map((e, i) => {
                const ts = new Date(e.created_at).toLocaleString();
                const source = e.source_id || 'unknown';
                const ruleId = e.rule_id || '—';
                const status = e.processing_path === 'fast' ? 'ok' : 'unresolved';
                
                let statusBadge;
                if (status === 'ok') statusBadge = <span className="badge ok">normalized</span>;
                else statusBadge = <span className="badge warn">adaptive (spot-check)</span>;

                return (
                  <React.Fragment key={e.id || i}>
                    <tr className="clickable" onClick={() => toggleDetail(i)}>
                      <td>{openDetail === i ? '▾' : '▸'}</td>
                      <td className="mono">{ts}</td>
                      <td>{source}</td>
                      <td className="mono">{ruleId}</td>
                      <td>{statusBadge}</td>
                      <td className="mono">{e.trace_id?.slice(0, 8) || '—'}</td>
                    </tr>
                    {openDetail === i && (
                      <tr className="detail-row open">
                        <td colSpan={6}>
                          <div className="detail-grid">
                            <div>
                              <label className="field-label">Raw event</label>
                              <div className="code-box">
                                {masked && e.masked_payload ? JSON.stringify(e.masked_payload, null, 2) : JSON.stringify(e.raw_payload || {}, null, 2)}
                              </div>
                            </div>
                            <div>
                              <label className="field-label">Normalized</label>
                              <div className="code-box">
                                {JSON.stringify(e.normalized_payload || {}, null, 2)}
                              </div>
                              <div className="trace">
                                raw <b>{e.trace_id?.slice(0, 8) || '—'}</b> → rule <b>{ruleId}</b> → normalized <b>{e.trace_id?.slice(0, 8) || '—'}-n</b>
                              </div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
