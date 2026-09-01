import { useState, useEffect, useCallback } from 'react';
import {
  fetchTraces, fetchTrace, fetchTraceTimeline, fetchTraceRaw,
  fetchTraceNormalized, fetchTraceProvenance, fetchTraceIntegrity,
} from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import {
  Search, Activity, GitCommit, Clock, Hash, Lock, Globe,
  RefreshCw, Loader2, ChevronRight, CheckCircle2, XCircle,
  Copy, Check, Code, List, FileText, Zap,
} from 'lucide-react';
import { cn } from '../utils/classnames';
import { formatIST } from '../utils/date';
import { VisualLineage } from '../components/explainability/VisualLineage';

type TraceItem = {
  trace_id: string;
  source_id: string;
  received_at: string;
  transport: string;
  byte_length: number;
  sha256?: string;
  status?: string;
  processing_path?: string;
  mapping_version?: number;
};

type StageRun = {
  stage: string;
  status: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  output_reference?: string;
  error_code?: string;
  error_message?: string;
};

export function TraceExplorer() {
  const [searchQuery, setSearchQuery] = useState('');
  const [traces, setTraces] = useState<TraceItem[]>([]);
  const [tracesLoading, setTracesLoading] = useState(true);

  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [traceDetail, setTraceDetail] = useState<any>(null);
  const [timeline, setTimeline] = useState<StageRun[]>([]);
  const [rawData, setRawData] = useState<any>(null);
  const [normalized, setNormalized] = useState<any>(null);
  const [provenance, setProvenance] = useState<any[]>([]);
  const [integrity, setIntegrity] = useState<any>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [hoveredField, setHoveredField] = useState<string | null>(null);
  const [normalizedView, setNormalizedView] = useState<'fields' | 'json'>('fields');
  const [copiedKey, setCopiedKey] = useState<string | null>(null);

  const copyText = (text: string, keyName: string) => {
    if (!text) return;
    navigator.clipboard.writeText(text);
    setCopiedKey(keyName);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  // Load trace list
  const loadTraces = useCallback(async () => {
    setTracesLoading(true);
    try {
      const data = await fetchTraces({ page: 1 });
      setTraces(data.items ?? []);
    } catch (e) {
      console.error('Failed to load traces:', e);
    } finally {
      setTracesLoading(false);
    }
  }, []);

  useEffect(() => { loadTraces(); }, [loadTraces]);

  // Load trace detail when selection changes
  useEffect(() => {
    if (!selectedId) return;
    (async () => {
      setDetailLoading(true);
      setTraceDetail(null); setTimeline([]); setRawData(null);
      setNormalized(null); setProvenance([]); setIntegrity(null);
      try {
        const [detail, tl, raw, integ, prov] = await Promise.allSettled([
          fetchTrace(selectedId),
          fetchTraceTimeline(selectedId),
          fetchTraceRaw(selectedId),
          fetchTraceIntegrity(selectedId),
          fetchTraceProvenance(selectedId),
        ]);

        if (detail.status === 'fulfilled')   setTraceDetail(detail.value);
        if (tl.status === 'fulfilled')       setTimeline(tl.value.stages ?? []);
        if (raw.status === 'fulfilled')      setRawData(raw.value);
        if (integ.status === 'fulfilled')    setIntegrity(integ.value);
        if (prov.status === 'fulfilled')     setProvenance(prov.value ?? []);

        // Try normalized (may 404 if not yet processed)
        try { setNormalized(await fetchTraceNormalized(selectedId)); } catch {}
      } catch (e) {
        console.error('Failed to load trace detail:', e);
      } finally {
        setDetailLoading(false);
      }
    })();
  }, [selectedId]);

  const filteredTraces = traces.filter(t =>
    !searchQuery ||
    t.trace_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    t.source_id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const copyHash = () => {
    if (integrity?.retrieved_digest) {
      navigator.clipboard.writeText(integrity.retrieved_digest);
    }
  };

  const normalizedFields = normalized?.normalized_payload
    ? flattenObject(normalized.normalized_payload)
    : {};

  const provenanceByField = provenance.reduce((acc: any, p: any) => {
    acc[p.normalized_field] = p;
    return acc;
  }, {});

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6 max-w-7xl mx-auto">
      {/* TRACE LIST */}
      <div className="w-72 shrink-0 flex flex-col gap-4 border-r border-slate-800 pr-6">
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <GitCommit className="w-5 h-5 text-brand-purple" />
          Trace Explorer
          <button onClick={loadTraces} className="ml-auto text-slate-500 hover:text-slate-300">
            <RefreshCw className={cn("w-4 h-4", tracesLoading && "animate-spin")} />
          </button>
        </h2>

        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search trace ID or source…"
            className="w-full bg-slate-900 border border-slate-700 rounded-md pl-8 p-2 text-sm text-slate-100 focus:border-brand-purple focus:ring-1 focus:ring-brand-purple outline-none"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {tracesLoading && (
            <div className="flex items-center justify-center py-12 text-slate-500">
              <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
            </div>
          )}
          {!tracesLoading && filteredTraces.length === 0 && (
            <div className="text-center py-12 text-slate-500 text-sm">
              No traces found. Ingest a log first.
            </div>
          )}
          {filteredTraces.map(t => (
            <div
              key={t.trace_id}
              onClick={() => setSelectedId(t.trace_id)}
              className={cn(
                "p-3 rounded-lg border cursor-pointer transition-colors",
                selectedId === t.trace_id
                  ? "bg-brand-purple/5 border-brand-purple/30"
                  : "bg-slate-900 border-slate-800 hover:border-slate-600"
              )}
            >
              <div className="flex justify-between items-start mb-1">
                <div className="text-xs font-mono text-brand-purple truncate max-w-[160px]">{t.trace_id.slice(0, 16)}…</div>
                <div className="text-[10px] text-slate-400 shrink-0 ml-1 font-mono">
                  {formatIST(t.received_at, 'compact')}
                </div>
              </div>
              <div className="text-xs text-slate-300 truncate">{t.source_id}</div>
              <div className="text-[10px] text-slate-500 mt-1">{t.byte_length} bytes · {t.transport}</div>
              <div className="mt-1.5 flex gap-1">
                <Badge
                  variant={t.status === 'normalized' ? 'success' : t.status === 'dead_letter' ? 'destructive' : 'secondary'}
                  className="text-[9px] px-1 py-0"
                >
                  {t.status ?? 'pending'}
                </Badge>
                {t.processing_path && (
                  <Badge variant="secondary" className="text-[9px] px-1 py-0">{t.processing_path}</Badge>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* TRACE WORKSPACE */}
      {selectedId ? (
        <div className="flex-1 flex flex-col gap-5 overflow-y-auto pr-2">
          {/* Header bar */}
          <div className="flex items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800 shrink-0">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-full bg-brand-purple/10 flex items-center justify-center">
                {detailLoading
                  ? <Loader2 className="w-5 h-5 text-brand-purple animate-spin" />
                  : <GitCommit className="w-5 h-5 text-brand-purple" />
                }
              </div>
              <div>
                <h2 className="text-slate-100 font-mono font-bold text-sm">{selectedId}</h2>
                <p className="text-slate-400 text-xs">
                  {traceDetail?.source_id} · {traceDetail?.transport} ·{' '}
                  {traceDetail?.processing_path ?? '—'} path
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={copyHash} disabled={!integrity?.retrieved_digest}>
                <Hash className="w-4 h-4 mr-1" /> Copy Hash
              </Button>
            </div>
          </div>

          {/* Processing Timeline */}
          {timeline.length > 0 && (
            <Card className="bg-slate-900 border-slate-800 shrink-0">
              <CardHeader className="pb-2">
                <CardTitle className="text-xs text-slate-400 uppercase tracking-widest flex items-center gap-2">
                  <Activity className="w-4 h-4" /> Processing Timeline
                </CardTitle>
              </CardHeader>
              <CardContent className="flex items-center gap-1 overflow-x-auto pb-2">
                {timeline.map((s, i) => (
                  <div key={i} className="flex items-center gap-1">
                    <div className={cn(
                      "flex flex-col items-center p-2 rounded-lg border min-w-[80px] text-center",
                      s.status === 'COMPLETE' ? "border-brand-green/30 bg-brand-green/5" :
                      s.status === 'FAILED'   ? "border-red-800/50 bg-red-900/10" :
                      "border-slate-700 bg-slate-800"
                    )}>
                      <div className={cn(
                        "text-[10px] font-bold uppercase",
                        s.status === 'COMPLETE' ? "text-brand-green" :
                        s.status === 'FAILED'   ? "text-red-400" : "text-slate-400"
                      )}>{s.stage}</div>
                      <div className="text-[10px] text-slate-500 mt-0.5">
                        {s.duration_ms ? `${s.duration_ms.toFixed(0)}ms` : '—'}
                      </div>
                    </div>
                    {i < timeline.length - 1 && <ChevronRight className="w-3 h-3 text-slate-700 shrink-0" />}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Raw / Normalized panel */}
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
            {/* RAW EVENT */}
            <Card className="bg-slate-900 border-slate-800 flex flex-col shadow-xl">
              <CardHeader className="border-b border-slate-800 pb-3 flex flex-row items-center justify-between py-3">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-sm font-bold text-slate-200 flex items-center gap-2">
                    <FileText className="w-4 h-4 text-slate-400" />
                    RAW EVENT
                  </CardTitle>
                  <Badge variant="secondary" className="font-mono text-[10px]">
                    {rawData?.byte_length ?? '—'} bytes
                  </Badge>
                </div>
                {rawData?.payload && (
                  <button
                    onClick={() => copyText(rawData.payload, 'raw')}
                    className="text-[11px] px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white font-semibold transition-all flex items-center gap-1 border border-white/20 shadow-sm"
                    title="Copy Raw Log Payload"
                  >
                    {copiedKey === 'raw' ? <Check className="w-3 h-3 text-brand-green" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedKey === 'raw' ? 'Copied' : 'Copy'}</span>
                  </button>
                )}
              </CardHeader>
              <CardContent className="p-4 bg-slate-950/90 font-mono text-xs leading-relaxed text-slate-200 select-all">
                {rawData?.payload ? (
                  <pre className="whitespace-pre-wrap break-all font-mono text-xs text-slate-300">
                    {rawData.payload}
                  </pre>
                ) : detailLoading ? (
                  <div className="flex items-center justify-center py-12 text-slate-500 gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-slate-400" /> Loading raw payload…
                  </div>
                ) : (
                  <div className="text-slate-600 italic py-6 text-center">No raw payload available</div>
                )}
              </CardContent>
            </Card>

            {/* NORMALIZED EVENT */}
            <Card className="bg-slate-900 border-slate-800 flex flex-col shadow-xl">
              <CardHeader className="border-b border-slate-800 pb-3 flex flex-row items-center justify-between py-3 gap-2">
                <div className="flex items-center gap-2">
                  <CardTitle className="text-sm font-bold text-brand-cyan flex items-center gap-2">
                    <Zap className="w-4 h-4 text-brand-cyan" />
                    NORMALIZED EVENT
                  </CardTitle>
                  {normalized ? (
                    <Badge variant="success" className="font-mono text-[10px]">
                      v{normalized.schema_version || 'ulpf-core-1.0'}
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="text-[10px]">pending</Badge>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {/* View mode toggle */}
                  <div className="flex bg-slate-950 border border-slate-800 rounded-lg p-0.5 text-xs">
                    <button
                      onClick={() => setNormalizedView('fields')}
                      className={cn(
                        "px-2.5 py-1 rounded font-semibold text-[11px] transition-all flex items-center gap-1",
                        normalizedView === 'fields'
                          ? "bg-white text-slate-950 shadow-sm"
                          : "text-slate-400 hover:text-white"
                      )}
                    >
                      <List className="w-3 h-3" />
                      <span>Fields ({Object.keys(normalizedFields).length})</span>
                    </button>
                    <button
                      onClick={() => setNormalizedView('json')}
                      className={cn(
                        "px-2.5 py-1 rounded font-semibold text-[11px] transition-all flex items-center gap-1",
                        normalizedView === 'json'
                          ? "bg-white text-slate-950 shadow-sm"
                          : "text-slate-400 hover:text-white"
                      )}
                    >
                      <Code className="w-3 h-3" />
                      <span>JSON</span>
                    </button>
                  </div>

                  {normalized?.normalized_payload && (
                    <button
                      onClick={() => copyText(JSON.stringify(normalized.normalized_payload, null, 2), 'normalized')}
                      className="text-[11px] px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-white font-semibold transition-all flex items-center gap-1 border border-white/20 shadow-sm"
                      title="Copy Formatted JSON"
                    >
                      {copiedKey === 'normalized' ? <Check className="w-3 h-3 text-brand-green" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedKey === 'normalized' ? 'Copied' : 'Copy'}</span>
                    </button>
                  )}
                </div>
              </CardHeader>

              <CardContent className="p-4 bg-slate-950/90">
                {normalized ? (
                  normalizedView === 'fields' ? (
                    <div className="space-y-2.5">
                      {Object.entries(normalizedFields).map(([key, val]) => {
                        const prov = provenanceByField[key];
                        return (
                          <div
                            key={key}
                            className={cn(
                              "flex flex-col md:flex-row md:items-start gap-3 p-3 rounded-lg transition-all border border-slate-800/80 bg-slate-900/60 hover:bg-slate-900 hover:border-brand-cyan/50",
                              hoveredField === key && "border-brand-cyan bg-brand-cyan/10 shadow-sm"
                            )}
                            onMouseEnter={() => setHoveredField(key)}
                            onMouseLeave={() => setHoveredField(null)}
                          >
                            {/* CANONICAL FIELD KEY - FULLY VISIBLE, CLEAN WORD WRAPPING */}
                            <div className="md:w-5/12 min-w-[200px] flex flex-col gap-1 shrink-0">
                              <span
                                className="text-brand-cyan font-mono text-xs font-bold break-words select-all leading-snug"
                                title={key}
                              >
                                {key}
                              </span>
                              {prov && (
                                <span
                                  className="text-[10px] font-mono text-slate-400 bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800 self-start inline-block"
                                  title={`Transformation: ${prov.transformation || 'direct'}`}
                                >
                                  src: {prov.source_field}
                                </span>
                              )}
                            </div>

                            {/* NORMALIZED VALUE - FULLY VISIBLE */}
                            <div className="flex-1 font-mono text-xs break-all bg-slate-950 p-2.5 rounded-md border border-slate-800 text-slate-100 select-all leading-relaxed">
                              {renderNormalizedValue(val)}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    /* PRETTY FORMATTED JSON VIEW */
                    <pre className="p-3.5 font-mono text-xs text-brand-green leading-relaxed whitespace-pre-wrap break-all bg-slate-950 rounded-lg border border-slate-800 select-all">
                      {JSON.stringify(normalized.normalized_payload, null, 2)}
                    </pre>
                  )
                ) : detailLoading ? (
                  <div className="flex items-center justify-center py-12 text-slate-500 gap-2">
                    <Loader2 className="w-4 h-4 animate-spin text-brand-cyan" /> Loading normalized event…
                  </div>
                ) : (
                  <div className="flex items-center justify-center py-12 text-slate-600 text-sm">
                    Event not yet normalized or pending mapping activation.
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Lineage + Integrity */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-5 pb-12">
            <Card className="bg-slate-900 border-slate-800 col-span-1 xl:col-span-2">
              <CardHeader>
                <CardTitle className="text-xs text-slate-400 uppercase tracking-widest">LINEAGE & PROVENANCE</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex justify-center py-2">
                  <VisualLineage
                    raw={`${traceDetail?.source_id ?? 'unknown'} · ${traceDetail?.byte_length ?? '—'}b`}
                    extracted={traceDetail?.transport ?? '—'}
                    type={traceDetail?.processing_path ?? 'adaptive'}
                    mapping={normalized?.mapping_version ? `Mapping v${normalized.mapping_version}` : 'pending'}
                    transformation={provenance.map((p: any) => p.transformation).filter(Boolean).join(', ') || 'direct'}
                    normalized={normalized?.schema_version ?? '—'}
                    provenance={integrity?.stored_digest ? `${integrity.stored_digest.slice(0, 20)}…` : '—'}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-slate-900 border-slate-800">
              <CardHeader>
                <CardTitle className="text-xs text-slate-400 uppercase tracking-widest">INTEGRITY</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-md border border-slate-800">
                  {integrity?.verified === true
                    ? <CheckCircle2 className="w-5 h-5 text-brand-green" />
                    : integrity?.verified === false
                      ? <XCircle className="w-5 h-5 text-brand-red" />
                      : <Lock className="w-5 h-5 text-slate-500" />
                  }
                  <div>
                    <div className="text-xs text-slate-400">SHA-256 Seal</div>
                    <div className={cn(
                      "text-sm font-medium",
                      integrity?.verified === true ? "text-brand-green" :
                      integrity?.verified === false ? "text-brand-red" : "text-slate-500"
                    )}>
                      {integrity?.verdict ?? (detailLoading ? '…' : 'Not checked')}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-md border border-slate-800">
                  <Globe className="w-5 h-5 text-brand-cyan" />
                  <div>
                    <div className="text-xs text-slate-400">Schema Version</div>
                    <div className="text-sm text-slate-200">{normalized?.schema_version ?? '—'}</div>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-md border border-slate-800">
                  <Clock className="w-5 h-5 text-slate-400" />
                  <div>
                    <div className="text-xs text-slate-400">Total Pipeline</div>
                    <div className="text-sm text-slate-200">
                      {timeline.reduce((sum, s) => sum + (s.duration_ms ?? 0), 0).toFixed(0)}ms
                    </div>
                  </div>
                </div>

                {integrity?.stored_digest && (
                  <div className="p-2 bg-slate-950 rounded border border-slate-800">
                    <div className="text-[10px] text-slate-500 mb-1">Stored digest</div>
                    <div className="font-mono text-[10px] text-slate-400 break-all">
                      {integrity.stored_digest}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-center max-w-md">
            <GitCommit className="w-12 h-12 text-slate-700 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-slate-300 mb-2">Select a trace</h2>
            <p className="text-slate-500">Choose a trace from the list to inspect raw payload, normalized event, processing timeline, and cryptographic integrity.</p>
          </div>
        </div>
      )}
    </div>
  );
}

function flattenObject(obj: any, prefix = ''): Record<string, any> {
  const result: Record<string, any> = {};
  for (const [k, v] of Object.entries(obj ?? {})) {
    const key = prefix ? `${prefix}.${k}` : k;
    if (v !== null && typeof v === 'object' && !Array.isArray(v)) {
      Object.assign(result, flattenObject(v, key));
    } else {
      result[key] = v;
    }
  }
  return result;
}

function renderNormalizedValue(val: any) {
  if (val === null || val === undefined) {
    return <span className="text-slate-500 italic">null</span>;
  }
  if (typeof val === 'boolean') {
    return <span className="text-brand-purple font-bold">{String(val)}</span>;
  }
  if (typeof val === 'number') {
    return <span className="text-brand-cyan font-bold">{val}</span>;
  }
  if (typeof val === 'string') {
    return <span className="text-emerald-300">"{val}"</span>;
  }
  return <span className="text-amber-200">{JSON.stringify(val)}</span>;
}
