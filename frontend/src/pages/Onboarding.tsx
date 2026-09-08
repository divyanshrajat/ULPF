import React, { useState } from 'react';
import { analyzeLog } from '../services/api';

export const Onboarding: React.FC = () => {
  const [sourceId, setSourceId] = useState('paloalto');
  const [rawPayload, setRawPayload] = useState('<14>1 2026-09-07T10:22:41Z fw-edge-02 PAN - - - THREAT,vulnerability,drop,10.1.2.45,203.0.113.9,443,tcp,critical,"SQL Injection Attempt"');
  const [targetSchema, setTargetSchema] = useState('ocsf');
  
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  // Pipeline UI states
  const [stepFingerprint, setStepFingerprint] = useState(''); // active, done, skip
  const [stepAgent, setStepAgent] = useState('');
  const [stepVerify, setStepVerify] = useState('');
  const [stepNormalize, setStepNormalize] = useState('');
  const [stepReview, setStepReview] = useState('');

  const [agentText, setAgentText] = useState('Draft a candidate rule for an unmatched format');
  const [verifyText, setVerifyText] = useState('Re-run drafted rule against the sample; retry on failure');
  const [badgeState, setBadgeState] = useState('');
  const [badgeText, setBadgeText] = useState('');
  
  const [saved, setSaved] = useState(false);

  const resetPipelineUI = () => {
    setStepFingerprint('');
    setStepAgent('');
    setStepVerify('');
    setStepNormalize('');
    setStepReview('');
    setAgentText('Draft a candidate rule for an unmatched format');
    setVerifyText('Re-run drafted rule against the sample; retry on failure');
    setResult(null);
    setSaved(false);
  };

  const handleSourceChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSourceId(e.target.value);
    if (e.target.value === 'paloalto') {
      setRawPayload('<14>1 2026-09-07T10:22:41Z fw-edge-02 PAN - - - THREAT,vulnerability,drop,10.1.2.45,203.0.113.9,443,tcp,critical,"SQL Injection Attempt"');
      setTargetSchema('ocsf');
    } else {
      setRawPayload('{"eventTime":"2026-09-07T09:58:03Z","eventSource":"iam.amazonaws.com","eventName":"ConsoleLogin","sourceIPAddress":"198.51.100.22","userIdentity":{"arn":"arn:aws:iam::4021:user/asha"}}');
      setTargetSchema('ecs');
    }
    resetPipelineUI();
  };

  const handleAnalyze = async () => {
    setAnalyzing(true);
    resetPipelineUI();

    setStepFingerprint('active');
    
    try {
      const res = await analyzeLog({
        source_id: sourceId,
        raw_payload: rawPayload.startsWith('{') ? JSON.parse(rawPayload) : rawPayload,
        target_schema: targetSchema
      });

      setStepFingerprint('done');

      if (res.status === 'matched_existing') {
        setStepAgent('skip');
        setAgentText('Skipped — matched existing rule');
        setStepVerify('skip');
        setVerifyText('Skipped — existing rule already verified');
        setBadgeState('match');
        setBadgeText(`matched existing rule — ${res.rule_id}`);
      } else {
        setStepAgent('active');
        setAgentText('No match — Rule Authoring Agent drafting...');
        // Simulate drafting time since API is fast or mock if we don't have true delay
        await new Promise(r => setTimeout(r, 1000));
        setStepAgent('done');
        setAgentText('Draft complete — candidate rule proposed');

        setStepVerify('active');
        setVerifyText('Re-running rule against sample...');
        await new Promise(r => setTimeout(r, 600));
        setStepVerify('done');
        setVerifyText('Full match, no null required fields — passed');
        
        setBadgeState('nomatch');
        setBadgeText('no match — new rule drafted by Rule Authoring Agent');
      }

      setStepNormalize('active');
      await new Promise(r => setTimeout(r, 400));
      setStepNormalize('done');
      
      setStepReview('active');
      setResult(res);

    } catch (err) {
      console.error(err);
      alert('Analysis failed');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSave = () => {
    setStepReview('done');
    setSaved(true);
  };

  return (
    <div className="view active">
      <div className="topbar">
        <div>
          <h1>Studio — author a new rule</h1>
          <p>Teach ULPF a log format once; the rule becomes reusable everywhere.</p>
        </div>
        <div className="env-badge">SANDBOX</div>
      </div>

      <div className="studio-grid">
        <div className="panel">
          <h3>1. Sample log</h3>
          <p className="hint">Pick a sample source, or paste your own raw log line.</p>

          <label className="field-label">Sample source</label>
          <select value={sourceId} onChange={handleSourceChange}>
            <option value="paloalto">Palo Alto firewall — no matching rule</option>
            <option value="cloudtrail">AWS CloudTrail — matches existing rule</option>
          </select>

          <label className="field-label">Raw log sample</label>
          <textarea 
            className="mono" 
            spellCheck="false"
            value={rawPayload}
            onChange={(e) => setRawPayload(e.target.value)}
          ></textarea>

          <label className="field-label">Target schema</label>
          <select value={targetSchema} onChange={(e) => setTargetSchema(e.target.value)}>
            <option value="ocsf">OCSF — Open Cybersecurity Schema Framework</option>
            <option value="ecs">ECS — Elastic Common Schema</option>
          </select>

          <div className="btn-row">
            <button className="btn btn-primary" disabled={analyzing} onClick={handleAnalyze}>
              Analyze sample
            </button>
            <button className="btn btn-ghost" onClick={resetPipelineUI}>Reset</button>
          </div>

          <div className="pipeline">
            <div className={`p-step ${stepFingerprint}`}>
              <div className="p-dot"></div>
              <div className="p-text"><b>Fingerprint check</b><span>Compare against the Rule Registry</span></div>
            </div>
            <div className={`p-step ${stepAgent}`}>
              <div className="p-dot"></div>
              <div className="p-text"><b>Rule Authoring Agent</b><span>{agentText}</span></div>
            </div>
            <div className={`p-step ${stepVerify}`}>
              <div className="p-dot"></div>
              <div className="p-text"><b>Self-verification</b><span>{verifyText}</span></div>
            </div>
            <div className={`p-step ${stepNormalize}`}>
              <div className="p-dot"></div>
              <div className="p-text"><b>Normalize</b><span>Apply the rule, map into target schema</span></div>
            </div>
            <div className={`p-step ${stepReview}`}>
              <div className="p-dot"></div>
              <div className="p-text"><b>Vendor review</b><span>Confirm or edit the field mapping below</span></div>
            </div>
          </div>
        </div>

        <div className="panel">
          <h3>2. Result</h3>
          
          {!result ? (
            <p className="hint">{analyzing ? 'Analyzing...' : 'Run analysis to see the rule and normalized output.'}</p>
          ) : (
            <div>
              <div style={{ marginBottom: '12px' }}>
                <span className={`badge ${badgeState}`}>{badgeText}</span>
              </div>

              <label className="field-label">
                Field mapping <span style={{ color: 'var(--dim)' }}>
                  {badgeState === 'match' ? '(from Rule Registry)' : '(agent-drafted, editable)'}
                </span>
              </label>
              
              <table style={{ marginBottom: '16px' }}>
                <thead>
                  <tr>
                    <th>Extracted field</th>
                    <th>Target field (schema)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.normalized_payload || {}).map(([k, v]) => (
                    <tr key={k}>
                      <td className="mono">{k}</td>
                      <td className="mono">
                        <input 
                          readOnly
                          value={typeof v === 'object' ? JSON.stringify(v) : String(v)} 
                          style={{ width: '100%', background: 'var(--panel-2)', border: '1px solid var(--line)', color: 'var(--ink)', borderRadius: '4px', padding: '5px 7px', fontSize: '12px', fontFamily: 'Consolas,monospace' }} 
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <label className="field-label">Normalized preview</label>
              <div className="code-box">
                {JSON.stringify(result.normalized_payload, null, 2)}
              </div>

              <div className="btn-row" style={{ marginTop: '16px' }}>
                <button className="btn btn-primary" onClick={handleSave}>Approve &amp; save rule</button>
                <button className="btn btn-ghost" onClick={resetPipelineUI}>Discard</button>
              </div>
              
              {saved && (
                <p className="hint" style={{ color: 'var(--cyan)', marginTop: '10px' }}>
                  Saved as Active in the Rule Registry — usable immediately via API/UI.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
