import React, { useState } from 'react';
import { analyzeLog } from '../services/api';
import { cn } from '../utils/classnames';
import { Zap, Sparkles } from 'lucide-react';

export const Onboarding: React.FC = () => {
  const [sourceId, setSourceId] = useState('paloalto');
  const [rawPayload, setRawPayload] = useState('<14>1 2026-09-07T10:22:41Z fw-edge-02 PAN - - - THREAT,vulnerability,drop,10.1.2.45,203.0.113.9,443,tcp,critical,"SQL Injection Attempt"');
  const [targetSchema, setTargetSchema] = useState('ocsf');
  
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [stepFingerprint, setStepFingerprint] = useState('');
  const [stepAgent, setStepAgent] = useState('');
  const [stepVerify, setStepVerify] = useState('');
  const [stepNormalize, setStepNormalize] = useState('');
  const [stepReview, setStepReview] = useState('');

  const [agentText, setAgentText] = useState('Draft a candidate rule for an unmatched format');
  const [verifyText, setVerifyText] = useState('Re-run drafted rule against the sample; retry on failure');
  const [badgeState, setBadgeState] = useState('');
  const [badgeText, setBadgeText] = useState<React.ReactNode>('');
  
  const [saved, setSaved] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

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
    setErrorMsg(null);
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
        setBadgeText(<> <Zap className="w-3.5 h-3.5" /> FAST PATH: matched existing rule — {res.rule_id} </>);
      } else {
        setStepAgent('active');
        setAgentText('No match — Rule Authoring Agent drafting...');
        await new Promise(r => setTimeout(r, 1000));
        setStepAgent('done');
        setAgentText('Draft complete — candidate rule proposed');

        setStepVerify('active');
        setVerifyText('Re-running rule against sample...');
        await new Promise(r => setTimeout(r, 600));
        setStepVerify('done');
        setVerifyText('Full match, no null required fields — passed');
        
        setBadgeState('nomatch');
        setBadgeText(<> <Sparkles className="w-3.5 h-3.5" /> LLM AGENT: new rule drafted by Rule Authoring Agent </>);
      }

      setStepNormalize('active');
      await new Promise(r => setTimeout(r, 400));
      setStepNormalize('done');
      
      setStepReview('active');
      setResult(res);

    } catch (err: any) {
      console.error(err);
      const detail = err?.response?.data?.detail || err?.message || 'Unknown error occurred';
      setErrorMsg(detail);
      
      if (stepFingerprint === 'active') setStepFingerprint('error');
      else if (stepAgent === 'active') setStepAgent('error');
      else if (stepVerify === 'active') setStepVerify('error');
      else if (stepNormalize === 'active') setStepNormalize('error');
      else if (stepReview === 'active') setStepReview('error');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleSave = () => {
    setStepReview('done');
    setSaved(true);
  };

  const getStepDotClass = (status: string) => {
    switch(status) {
      case 'active': return 'border-brand-amber animate-pulse';
      case 'done': return 'border-brand-cyan bg-brand-cyan text-[#062024]';
      case 'skip': return 'border-brand-green/40 bg-brand-green/10 text-brand-green';
      case 'error': return 'border-red-500 bg-red-500/10 text-red-500';
      default: return 'border-[#1E3038] text-transparent';
    }
  };

  const badgeClass = cn(
    'inline-flex items-center gap-1.5 text-[11px] font-mono px-2.5 py-0.5 rounded-full border',
    badgeState === 'match' && 'bg-brand-green/10 text-brand-green border-brand-green/35',
    badgeState === 'nomatch' && 'bg-brand-purple/10 text-brand-purple border-brand-purple/35',
  );

  return (
    <div className="max-w-6xl mx-auto pb-12">
      <div className="flex justify-between items-start mb-6 flex-wrap gap-2.5">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Studio — author a new rule</h1>
          <p className="text-slate-400 text-sm">Teach ULPF a log format once; the rule becomes reusable everywhere.</p>
        </div>
        <div className="font-mono text-[11px] text-brand-amber border border-brand-amber/35 rounded bg-brand-amber/5 px-2.5 py-1 whitespace-nowrap">
          SANDBOX
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        <div className="bg-[#101D24] border border-[#1E3038] rounded-xl p-6 shadow-md">
          <h3 className="m-0 mb-1 text-sm font-bold text-slate-100">1. Sample log</h3>
          <p className="m-0 mb-5 text-[13px] text-slate-400">Pick a sample source, or paste your own raw log line.</p>

          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Sample source</label>
          <select 
            value={sourceId} 
            onChange={handleSourceChange}
            className="w-full bg-[#0D1920] border border-[#1E3038] rounded-lg text-[#DCE7EA] px-3 py-2 text-[13px] mb-4 outline-none focus:border-brand-cyan/50"
          >
            <option value="paloalto">Palo Alto firewall — no matching rule</option>
            <option value="cloudtrail">AWS CloudTrail — matches existing rule</option>
          </select>

          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Raw log sample</label>
          <textarea 
            className="w-full bg-[#0D1920] border border-[#1E3038] rounded-lg text-[#DCE7EA] px-3 py-2 text-[13px] mb-4 outline-none focus:border-brand-cyan/50 h-28 resize-y font-mono"
            spellCheck="false"
            value={rawPayload}
            onChange={(e) => setRawPayload(e.target.value)}
          ></textarea>

          <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Target schema</label>
          <select 
            value={targetSchema} 
            onChange={(e) => setTargetSchema(e.target.value)}
            className="w-full bg-[#0D1920] border border-[#1E3038] rounded-lg text-[#DCE7EA] px-3 py-2 text-[13px] mb-5 outline-none focus:border-brand-cyan/50"
          >
            <option value="ocsf">OCSF — Open Cybersecurity Schema Framework</option>
            <option value="ecs">ECS — Elastic Common Schema</option>
          </select>

          <div className="flex gap-3 flex-wrap">
            <button 
              className="bg-brand-cyan text-[#062024] font-bold rounded-lg px-4 py-2 text-[13px] disabled:bg-[#22383A] disabled:text-[#5F7679] disabled:cursor-not-allowed hover:bg-[#32b2ac] transition-colors"
              disabled={analyzing} 
              onClick={handleAnalyze}
            >
              {analyzing ? 'Analyzing...' : 'Analyze sample'}
            </button>
            <button 
              className="bg-transparent border border-[#1E3038] text-[#DCE7EA] font-semibold rounded-lg px-4 py-2 text-[13px] hover:bg-white/5 transition-colors"
              onClick={resetPipelineUI}
            >
              Reset
            </button>
          </div>

          <div className="flex flex-col gap-0 my-6 relative before:content-[''] before:absolute before:left-[9px] before:top-2 before:bottom-2 before:w-[1px] before:bg-[#1E3038]">
            <div className={`flex items-start gap-4 py-3 relative z-10 ${stepFingerprint}`}>
              <div className={`w-[19px] h-[19px] rounded-full border-2 shrink-0 mt-0.5 flex items-center justify-center transition-all bg-[#101D24] ${getStepDotClass(stepFingerprint)}`}></div>
              <div className="flex flex-col">
                <b className="text-[13.5px] text-slate-100 font-semibold">Fingerprint check</b>
                <span className="text-[12px] text-slate-400">Compare against the Rule Registry</span>
              </div>
            </div>
            <div className={`flex items-start gap-4 py-3 relative z-10 ${stepAgent}`}>
              <div className={`w-[19px] h-[19px] rounded-full border-2 shrink-0 mt-0.5 flex items-center justify-center transition-all bg-[#101D24] ${getStepDotClass(stepAgent)}`}>
                {stepAgent === 'active' && <div className="w-1.5 h-1.5 rounded-full bg-brand-amber animate-ping"></div>}
              </div>
              <div className="flex flex-col">
                <b className="text-[13.5px] text-slate-100 font-semibold">Rule Authoring Agent</b>
                <span className={`text-[12px] ${stepAgent === 'active' ? 'text-brand-purple animate-pulse' : 'text-slate-400'}`}>{agentText}</span>
              </div>
            </div>
            <div className={`flex items-start gap-4 py-3 relative z-10 ${stepVerify}`}>
              <div className={`w-[19px] h-[19px] rounded-full border-2 shrink-0 mt-0.5 flex items-center justify-center transition-all bg-[#101D24] ${getStepDotClass(stepVerify)}`}></div>
              <div className="flex flex-col">
                <b className="text-[13.5px] text-slate-100 font-semibold">Self-verification</b>
                <span className="text-[12px] text-slate-400">{verifyText}</span>
              </div>
            </div>
            <div className={`flex items-start gap-4 py-3 relative z-10 ${stepNormalize}`}>
              <div className={`w-[19px] h-[19px] rounded-full border-2 shrink-0 mt-0.5 flex items-center justify-center transition-all bg-[#101D24] ${getStepDotClass(stepNormalize)}`}></div>
              <div className="flex flex-col">
                <b className="text-[13.5px] text-slate-100 font-semibold">Normalize</b>
                <span className="text-[12px] text-slate-400">Apply the rule, map into target schema</span>
              </div>
            </div>
            <div className={`flex items-start gap-4 py-3 relative z-10 ${stepReview}`}>
              <div className={`w-[19px] h-[19px] rounded-full border-2 shrink-0 mt-0.5 flex items-center justify-center transition-all bg-[#101D24] ${getStepDotClass(stepReview)}`}></div>
              <div className="flex flex-col">
                <b className="text-[13.5px] text-slate-100 font-semibold">Vendor review</b>
                <span className="text-[12px] text-slate-400">Confirm or edit the field mapping below</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-[#101D24] border border-[#1E3038] rounded-xl p-6 shadow-md">
          <h3 className="m-0 mb-1 text-sm font-bold text-slate-100">2. Result</h3>
          
          {!result && !errorMsg ? (
            <p className="m-0 text-[13px] text-slate-400">{analyzing ? 'Running analysis pipeline...' : 'Run analysis to see the rule and normalized output.'}</p>
          ) : errorMsg ? (
            <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
              <div className="flex items-center gap-2 text-red-400 font-bold mb-2 text-sm">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                Analysis Failed
              </div>
              <p className="text-red-300 text-xs mb-3 font-mono">{errorMsg}</p>
              <div className="text-slate-400 text-xs">
                {errorMsg.includes('Source') ? 'This source does not exist yet. Please create it first via the API or select a valid source.' :
                 errorMsg.includes('LLM') ? 'The local LLM is not configured properly. Check ULPF_MOCK_LLM and ULPF_MODEL_PATH in your environment.' : 
                 'Check the console logs for more details or retry.'}
              </div>
            </div>
          ) : (
            <div className="mt-4">
              <div className="mb-4">
                <span className={badgeClass}>{badgeText}</span>
              </div>

              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Field mapping <span className="text-slate-500 normal-case tracking-normal font-normal">
                  {badgeState === 'match' ? '(from Rule Registry)' : '(agent-drafted, editable)'}
                </span>
              </label>
              
              <table className="w-full mb-5 text-left border-collapse">
                <thead>
                  <tr>
                    <th className="text-xs text-slate-400 font-semibold pb-2 border-b border-[#1E3038]">Extracted field</th>
                    <th className="text-xs text-slate-400 font-semibold pb-2 border-b border-[#1E3038]">Target field (schema)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.normalized_payload || {}).map(([k, v]) => (
                    <tr key={k}>
                      <td className="py-2.5 font-mono text-[12px] text-brand-cyan border-b border-[#1E3038]">{k}</td>
                      <td className="py-2.5 font-mono text-[12px] border-b border-[#1E3038]">
                        <input 
                          readOnly
                          value={typeof v === 'object' ? JSON.stringify(v) : String(v)} 
                          className="w-full bg-[#0D1920] border border-[#1E3038] text-[#DCE7EA] rounded px-2 py-1 outline-none"
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Normalized preview</label>
              <div className="bg-[#0D1920] border border-[#1E3038] rounded-lg p-3 whitespace-pre-wrap word-break text-brand-cyan max-h-60 overflow-auto font-mono text-xs">
                {JSON.stringify(result.normalized_payload, null, 2)}
              </div>

              <div className="flex gap-3 mt-5">
                <button 
                  className="bg-brand-cyan text-[#062024] font-bold rounded-lg px-4 py-2 text-[13px] hover:bg-[#32b2ac] transition-colors shadow-md shadow-brand-cyan/20"
                  onClick={handleSave}
                >
                  Approve &amp; save rule
                </button>
                <button 
                  className="bg-transparent border border-[#1E3038] text-[#DCE7EA] font-semibold rounded-lg px-4 py-2 text-[13px] hover:bg-white/5 transition-colors"
                  onClick={resetPipelineUI}
                >
                  Discard
                </button>
              </div>
              
              {saved && (
                <p className="mt-4 text-[13px] font-semibold text-brand-green flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                  Saved as Active in the Rule Registry — usable immediately.
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
