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
          <div className="grid grid-cols-2 gap-5" style={{ minHeight: 260 }}>
            {/* RAW */}
            <Card className="bg-slate-900 border-slate-800 flex flex-col">
              <CardHeader className="border-b border-slate-800 pb-3 flex flex-row items-center justify-between py-3">
                <CardTitle className="text-sm text-slate-300">RAW EVENT</CardTitle>
                <Badge variant="secondary">{rawData?.byte_length ?? '—'} bytes</Badge>
              </CardHeader>
              <CardContent className="p-4 flex-1 overflow-auto bg-slate-950 font-mono text-xs leading-relaxed text-slate-300 break-all">
                {rawData?.payload ?? (detailLoading ? <Loader2 className="w-4 h-4 animate-spin text-slate-500" /> : '—')}
              </CardContent>
            </Card>

            {/* NORMALIZED */}
            <Card className="bg-slate-900 border-slate-800 flex flex-col">
              <CardHeader className="border-b border-slate-800 pb-3 flex flex-row items-center justify-between py-3">
                <CardTitle className="text-sm text-brand-cyan">NORMALIZED EVENT</CardTitle>
                {normalized
                  ? <Badge variant="success">v{normalized.schema_version}</Badge>
                  : <Badge variant="secondary">pending</Badge>
                }
              </CardHeader>
              <CardContent className="p-4 flex-1 overflow-auto bg-slate-950">
                {normalized ? (
                  <div className="space-y-0.5">
                    {Object.entries(normalizedFields).map(([key, val]) => {
                      const prov = provenanceByField[key];
                      return (
                        <div
                          key={key}
                          className={cn(
                            "flex hover:bg-slate-800/50 rounded transition-colors px-2 py-1 cursor-default group",
                            hoveredField === key && "bg-brand-cyan/5"
                          )}
                          onMouseEnter={() => setHoveredField(key)}
                          onMouseLeave={() => setHoveredField(null)}
                          title={prov ? `Source: ${prov.source_field} → ${prov.transformation}` : ''}
                        >
                          <div className="w-2/5 text-brand-cyan font-mono text-xs truncate">{key}:</div>
                          <div className="w-3/5 text-slate-300 font-mono text-xs pl-2 truncate">
                            {typeof val === 'string' ? `"${val}"` : JSON.stringify(val)}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-full text-slate-600 text-sm">
                    {detailLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Not yet normalized'}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Lineage + Integrity */}
          <div className="grid grid-cols-3 gap-5">
            <Card className="bg-slate-900 border-slate-800 col-span-2">
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
