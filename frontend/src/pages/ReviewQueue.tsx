import { useState, useEffect, useCallback } from 'react';
import {
  fetchReviews, approveReview, rejectReview,
} from '../services/api';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  AlertTriangle, Filter, Search, ArrowRight,
  CheckCircle2, RefreshCw, Loader2, Check, X,
} from 'lucide-react';
import { cn } from '../utils/classnames';

type Proposal = {
  source_field: string;
  position?: string | number;
  inferred_type?: string;
  sample_value?: string;
  proposed_target: string;
  confidence: number;
  decision: string;
  signals?: { name: number; value: number; context: number; history: number };
};

type ReviewItem = {
  review_id: string;
  source_id: string;
  template_id: string;
  field_id?: string;
  pattern: string;
  proposals: Proposal[];
  confidence: number;
  reason?: string;
  priority?: number;
  status: string;
  assigned_to?: string;
  created_at?: string;
  reviewed_at?: string;
};

type Filter_ = 'all' | 'high_risk' | 'drift';

export function ReviewQueue() {
  const [queue, setQueue] = useState<ReviewItem[]>([]);
  const [activeReview, setActiveReview] = useState<ReviewItem | null>(null);
  const [filter, setFilter] = useState<Filter_>('all');
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldOverrides, setFieldOverrides] = useState<Record<string, string>>({}); // source_field → chosen_target
  const [fieldDecisions, setFieldDecisions] = useState<Record<string, 'accept' | 'reassign' | 'extension'>>({});
  const [search, setSearch] = useState('');

  const loadQueue = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchReviews({ status: filter === 'all' ? 'PENDING' : undefined });
      let items: ReviewItem[] = data.items ?? [];
      if (filter === 'high_risk') items = items.filter(i => i.confidence < 0.75);
      if (filter === 'drift')     items = items.filter(i => i.pattern?.startsWith('DRIFT:'));
      if (search) items = items.filter(i =>
        i.source_id.toLowerCase().includes(search.toLowerCase()) ||
        i.pattern?.toLowerCase().includes(search.toLowerCase())
      );
      setQueue(items);
      if (items.length > 0 && !activeReview) setActiveReview(items[0]);
    } catch (e: any) {
      setError(e?.message ?? 'Failed to load review queue');
    } finally {
      setLoading(false);
    }
  }, [filter, search]);

  useEffect(() => { loadQueue(); }, [loadQueue]);

  // Reset field state when active review changes
  useEffect(() => {
    if (!activeReview) return;
    const overrides: Record<string, string> = {};
    const decisions: Record<string, 'accept' | 'reassign' | 'extension'> = {};
    for (const p of (activeReview.proposals ?? [])) {
      overrides[p.source_field] = p.proposed_target;
      decisions[p.source_field] = 'accept';
    }
    setFieldOverrides(overrides);
    setFieldDecisions(decisions);
  }, [activeReview?.review_id]);

  const handleApprove = async () => {
    if (!activeReview) return;
    setActionLoading(true);
    try {
      // Build final bindings from per-field decisions
      const bindings: Record<string, string> = {};
      for (const p of activeReview.proposals) {
        const decision = fieldDecisions[p.source_field] ?? 'accept';
        if (decision === 'extension') continue; // Don't bind extension-only fields
        bindings[p.source_field] = fieldOverrides[p.source_field] ?? p.proposed_target;
      }
      await approveReview(activeReview.review_id, bindings);
      setActiveReview(null);
      await loadQueue();
    } catch (e: any) {
      setError(e?.message ?? 'Failed to approve mapping');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!activeReview) return;
    setActionLoading(true);
    try {
      await rejectReview(activeReview.review_id);
      setActiveReview(null);
      await loadQueue();
    } catch (e: any) {
      setError(e?.message ?? 'Failed to reject');
    } finally {
      setActionLoading(false);
    }
  };

  const handleMarkExtension = async (sourceField: string) => {
    if (!activeReview) return;
    setFieldDecisions(prev => ({ ...prev, [sourceField]: 'extension' }));
  };

  const handleReassign = (sourceField: string, newTarget: string) => {
    setFieldOverrides(prev => ({ ...prev, [sourceField]: newTarget }));
    setFieldDecisions(prev => ({ ...prev, [sourceField]: 'reassign' }));
  };

  const formatTime = (ts?: string) => {
    if (!ts) return '—';
    const d = new Date(ts);
    return d.toLocaleTimeString();
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6">
      {/* LEFT: QUEUE LIST */}
      <div className="w-[320px] shrink-0 flex flex-col gap-4 border-r border-slate-800 pr-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            Review Queue
            <Badge variant="warning">{queue.length}</Badge>
          </h2>
          <button onClick={loadQueue} className="text-slate-500 hover:text-slate-300 transition-colors">
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          </button>
        </div>

        {/* Search */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search source or pattern…"
            value={search}
            onChange={e => setSearch(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded-md pl-8 p-2 text-sm text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan outline-none"
          />
        </div>

        {/* Filter tabs */}
        <div className="flex gap-1.5 text-xs pb-0">
          {(['all', 'high_risk', 'drift'] as Filter_[]).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                "px-3 py-1.5 rounded-md transition-all border font-semibold",
                filter === f
                  ? "text-slate-950 bg-white border-white shadow-sm"
                  : "text-white bg-white/10 border-white/20 hover:bg-white/20"
              )}
            >
              {f === 'all' ? 'All' : f === 'high_risk' ? 'High Risk' : 'Drift'}
            </button>
          ))}
        </div>

        {error && (
          <div className="p-3 bg-red-900/30 border border-red-800/50 rounded-lg text-red-300 text-xs">
            {error}
          </div>
        )}

        <div className="flex-1 overflow-y-auto space-y-3 pr-2">
          {loading && (
            <div className="flex items-center justify-center py-12 text-slate-500">
              <Loader2 className="w-5 h-5 animate-spin mr-2" /> Loading…
            </div>
          )}
          {!loading && queue.length === 0 && (
            <div className="text-center p-8 bg-slate-900 border border-slate-800 rounded-lg">
              <CheckCircle2 className="w-8 h-8 text-brand-green mx-auto mb-3" />
              <h3 className="text-slate-300 font-medium">No pending reviews</h3>
              <p className="text-slate-500 text-sm mt-1">All mappings have been validated.</p>
            </div>
          )}
          {queue.map(item => (
            <Card
              key={item.review_id}
              className={cn(
                "cursor-pointer transition-colors",
                activeReview?.review_id === item.review_id
                  ? 'border-brand-cyan/50 bg-brand-cyan/5'
                  : 'bg-slate-900 border-slate-800 hover:border-slate-600'
              )}
              onClick={() => setActiveReview(item)}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-semibold text-slate-400 truncate max-w-[160px]">{item.source_id}</div>
                  <Badge variant={item.confidence >= 0.75 ? 'secondary' : 'warning'} className="text-[10px] px-1.5 py-0 shrink-0">
                    {(item.confidence * 100).toFixed(0)}%
                  </Badge>
                </div>
                <div className="text-xs font-mono text-slate-200 truncate mb-2" title={item.pattern}>{item.pattern || '—'}</div>
                <div className="flex items-center gap-3 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <AlertTriangle className="w-3 h-3 text-brand-amber" />
                    {item.proposals?.length || 0} fields
                  </span>
                  <span>{formatTime(item.created_at)}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* RIGHT: REVIEW WORKSPACE */}
      {activeReview ? (
        <div className="flex-1 flex flex-col gap-5 overflow-y-auto pr-2">
          {/* Header */}
          <div className="flex items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800 shrink-0">
            <div>
              <h2 className="text-slate-100 font-bold">{activeReview.source_id}</h2>
              <p className="text-slate-400 text-sm">
                Reviewing {activeReview.proposals?.length ?? 0} AI mapping proposals
                {activeReview.reason && <> · <span className="text-slate-500">{activeReview.reason}</span></>}
              </p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline" onClick={handleReject} disabled={actionLoading}>
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <X className="w-4 h-4 mr-1" />}
                Reject
              </Button>
              <Button variant="default" onClick={handleApprove} disabled={actionLoading} className="bg-white text-slate-950 font-bold hover:bg-slate-100 shadow-md">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4 mr-1" />}
                Approve Mapping
              </Button>
            </div>
          </div>

          {/* Pattern context */}
          <div className="bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 font-mono text-xs text-slate-400 break-all shrink-0">
            <span className="text-slate-600 mr-2">TEMPLATE:</span>
            {activeReview.pattern || '—'}
          </div>

          {/* Field proposals */}
          <div className="space-y-4">
            {(activeReview.proposals ?? []).map((p, i) => {
              const decision = fieldDecisions[p.source_field] ?? 'accept';
              const effectiveTarget = fieldOverrides[p.source_field] ?? p.proposed_target;
              return (
                <div key={i} className={cn(
                  "grid grid-cols-3 gap-4 bg-slate-900 p-4 rounded-xl border transition-colors",
                  decision === 'accept' ? "border-slate-800" :
                  decision === 'extension' ? "border-brand-purple/30" : "border-brand-amber/30"
                )}>
                  {/* SOURCE EVIDENCE */}
                  <div className="space-y-3 pr-4 border-r border-slate-800">
                    <div className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">Source Evidence</div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Extracted Field</div>
                      <div className="font-mono text-sm text-slate-100 bg-slate-950 p-2 rounded border border-slate-800 inline-block">
                        {p.source_field}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Inferred Type</div>
                      <Badge variant="secondary" className="font-mono">{p.inferred_type || 'text'}</Badge>
                    </div>
                    {p.sample_value && (
                      <div>
                        <div className="text-xs text-slate-400 mb-1">Sample Value</div>
                        <div className="font-mono text-xs text-slate-300 truncate max-w-[160px]" title={p.sample_value}>
                          "{p.sample_value}"
                        </div>
                      </div>
                    )}
                  </div>

                  {/* AI PROPOSAL */}
                  <div className="space-y-3 pr-4 border-r border-slate-800">
                    <div className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">AI Proposal</div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Canonical Target</div>
                      <div className="font-mono text-sm text-brand-purple bg-slate-950 p-2 rounded border border-slate-800 inline-block">
                        {effectiveTarget}
                      </div>
                    </div>
                    <div>
                      <div className="text-xs text-slate-400 mb-1">Confidence Score</div>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div className="h-full bg-brand-cyan" style={{ width: `${(p.confidence || 0) * 100}%` }} />
                        </div>
                        <span className="text-xs font-mono text-slate-300">{((p.confidence || 0) * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    {p.signals && (
                      <div className="text-[10px] font-mono text-slate-500 space-y-0.5">
                        {Object.entries(p.signals).map(([sig, val]: any) => (
                          <div key={sig}>{sig}: {(val * 100).toFixed(0)}%</div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* HUMAN DECISION */}
                  <div className="space-y-3">
                    <div className="text-[10px] font-bold tracking-widest text-brand-green uppercase">
                      Human Decision
                    </div>
                    <div className="space-y-2">
                      <button
                        onClick={() => setFieldDecisions(prev => ({ ...prev, [p.source_field]: 'accept' }))}
                        className={cn(
                          "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm border font-semibold transition-all",
                          decision === 'accept'
                            ? "text-brand-green bg-brand-green/20 border-brand-green shadow-sm"
                            : "text-white bg-white/10 border-white/20 hover:bg-white/20"
                        )}
                      >
                        <CheckCircle2 className="w-4 h-4" /> Accept Proposal
                      </button>

                      <ReassignInput
                        active={decision === 'reassign'}
                        currentTarget={effectiveTarget}
                        onReassign={(t) => handleReassign(p.source_field, t)}
                      />

                      <button
                        onClick={() => handleMarkExtension(p.source_field)}
                        className={cn(
                          "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm border font-semibold transition-all",
                          decision === 'extension'
                            ? "text-brand-purple bg-brand-purple/20 border-brand-purple shadow-sm"
                            : "text-white bg-white/10 border-white/20 hover:bg-white/20"
                        )}
                      >
                        <ArrowRight className="w-4 h-4" /> Extension Only
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-slate-900 border border-slate-800 rounded-xl">
          <div className="text-center max-w-md">
            <Filter className="w-12 h-12 text-slate-700 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-slate-300 mb-2">Select a review item</h2>
            <p className="text-slate-500">Choose an item from the queue to review AI mapping proposals and provide human feedback.</p>
          </div>
        </div>
      )}
    </div>
  );
}

function ReassignInput({ active, currentTarget, onReassign }: {
  active: boolean;
  currentTarget: string;
  onReassign: (target: string) => void;
}) {
  const [open, setOpen] = useState(false);
  const [value, setValue] = useState(currentTarget);

  const apply = () => {
    if (value.trim()) { onReassign(value.trim()); setOpen(false); }
  };

  if (!open) {
    return (
      <button
        onClick={() => { setOpen(true); setValue(currentTarget); }}
        className={cn(
          "w-full flex items-center gap-2 px-3 py-2 rounded-md text-sm border font-semibold transition-all",
          active
            ? "text-brand-amber bg-brand-amber/20 border-brand-amber shadow-sm"
            : "text-white bg-white/10 border-white/20 hover:bg-white/20"
        )}
      >
        <Search className="w-4 h-4" /> Reassign Target
      </button>
    );
  }

  return (
    <div className="space-y-1.5">
      <input
        autoFocus
        type="text"
        value={value}
        onChange={e => setValue(e.target.value)}
        onKeyDown={e => { if (e.key === 'Enter') apply(); if (e.key === 'Escape') setOpen(false); }}
        placeholder="target.field.name"
        className="w-full bg-slate-950 border border-brand-amber rounded-md p-2 text-xs font-mono text-slate-100 focus:outline-none"
      />
      <div className="flex gap-2">
        <Button size="sm" onClick={apply} className="bg-white text-slate-950 hover:bg-slate-100 font-bold text-xs h-7">
          Apply
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setOpen(false)} className="text-xs h-7 text-white hover:bg-white/10">
          Cancel
        </Button>
      </div>
    </div>
  );
}
