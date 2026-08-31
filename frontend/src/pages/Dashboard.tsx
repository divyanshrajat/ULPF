import { useState, useEffect, useCallback } from 'react';
import { fetchStats, fetchHealth } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ArrowRight, GitCommit, FileText, CheckCircle2, AlertTriangle, Zap, Network, RefreshCw } from 'lucide-react';
import { cn } from '../utils/classnames';

type Stats = {
  events_ingested: number;
  events_normalized: number;
  events_processed: number;
  fast_events: number;
  adaptive_events: number;
  review_pending: number;
  dead_letters: number;
  preservation_success: number;
  integrity_failures: number;
};

const EMPTY_STATS: Stats = {
  events_ingested: 0,
  events_normalized: 0,
  events_processed: 0,
  fast_events: 0,
  adaptive_events: 0,
  review_pending: 0,
  dead_letters: 0,
  preservation_success: 0,
  integrity_failures: 0,
};

export function Dashboard() {
  const [stats, setStats] = useState<Stats>(EMPTY_STATS);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRefresh, setLastRefresh] = useState<Date>(new Date());

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [statsData, healthData] = await Promise.all([
        fetchStats(),
        fetchHealth().catch(() => null),
      ]);
      setStats({ ...EMPTY_STATS, ...statsData });
      setHealth(healthData);
      setLastRefresh(new Date());
    } catch (e: any) {
      setError(e?.message || 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const interval = setInterval(load, 30_000); // Auto-refresh every 30s
    return () => clearInterval(interval);
  }, [load]);

  const systemStatus = health?.overall ?? 'unknown';

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      {/* HEADER */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-2">ULPF PIPELINE</h1>
          <p className="text-slate-400">Adaptive preprocessing for heterogeneous logs</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge
            variant={systemStatus === 'healthy' ? 'success' : systemStatus === 'degraded' ? 'warning' : 'secondary'}
            className="gap-1.5"
          >
            <div className={cn(
              "w-1.5 h-1.5 rounded-full",
              systemStatus === 'healthy' ? "bg-brand-green animate-pulse" :
              systemStatus === 'degraded' ? "bg-brand-amber animate-pulse" : "bg-slate-500"
            )} />
            {loading ? 'Connecting…' : systemStatus === 'healthy' ? 'Operational' : systemStatus === 'degraded' ? 'Degraded' : 'Unknown'}
          </Badge>
          <button
            onClick={load}
            className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            <RefreshCw className={cn("w-3 h-3", loading && "animate-spin")} />
            Refreshed {lastRefresh.toLocaleTimeString()}
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-brand-red/10 border border-brand-red/30 rounded-xl text-brand-red text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error} — backend may be starting up
        </div>
      )}

      {/* PIPELINE VISUALIZATION */}
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-4">Pipeline Overview</h2>
        <div className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-xl p-6 overflow-x-auto">
          <PipelineStage name="INGEST"    count={stats.events_ingested}    status="success" icon={FileText} />
          <PipelineArrow />
          <PipelineStage name="PRESERVE"  count={stats.preservation_success} status="success" icon={DbIcon} />
          <PipelineArrow />
          <PipelineStage name="DISCOVER"  count={stats.adaptive_events}    status="success" icon={SearchIcon} />
          <PipelineArrow />
          <PipelineStage name="MAP"       count={stats.events_processed}   status="success" icon={Network} />
          <PipelineArrow />
          <PipelineStage
            name="REVIEW"
            count={stats.review_pending}
            status={stats.review_pending > 0 ? 'warning' : 'success'}
            icon={AlertTriangle}
          />
          <PipelineArrow />
          <PipelineStage name="NORMALIZE" count={stats.events_normalized}  status="success" icon={CheckCircle2} />
          <PipelineArrow />
          <PipelineStage name="TRACE"     count={stats.events_normalized}  status="success" icon={GitCommit} />
        </div>
      </section>

      {/* ADAPTIVE VS FAST PATH */}
      <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="bg-slate-900 border-slate-800 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-brand-purple/5 rounded-full blur-3xl" />
          <CardHeader>
            <CardTitle className="text-brand-purple flex items-center gap-2">
              <Network className="w-5 h-5" />
              ADAPTIVE PATH
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-mono text-slate-100 mb-2">{stats.adaptive_events.toLocaleString()}</div>
            <p className="text-sm text-slate-400 mb-4">events processed via intelligent discovery</p>
            <ul className="space-y-2 text-sm text-slate-300">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-slate-600" /> Unknown format</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-slate-600" /> Template discovery</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-slate-600" /> Semantic mapping</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-brand-amber" /> Human review</li>
            </ul>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-32 h-32 bg-brand-cyan/5 rounded-full blur-3xl" />
          <CardHeader>
            <CardTitle className="text-brand-cyan flex items-center gap-2">
              <Zap className="w-5 h-5" />
              FAST PATH
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-mono text-slate-100 mb-2">{stats.fast_events.toLocaleString()}</div>
            <p className="text-sm text-slate-400 mb-4">events processed deterministically</p>
            <ul className="space-y-2 text-sm text-slate-300">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-brand-green" /> Known template</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-brand-green" /> Approved mapping</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-brand-green" /> Deterministic</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-slate-600" /> No remapping needed</li>
            </ul>
          </CardContent>
        </Card>
      </section>

      {/* METRICS */}
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-4">System Metrics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard title="Ingested" value={stats.events_ingested} />
          <MetricCard title="Normalized" value={stats.events_normalized} />
          <MetricCard title="Review Pending" value={stats.review_pending} type={stats.review_pending > 0 ? 'warning' : 'default'} />
          <MetricCard title="Dead Letters" value={stats.dead_letters} type={stats.dead_letters > 0 ? 'error' : 'success'} />
        </div>
      </section>

      {/* COMPONENT HEALTH */}
      {health && (
        <section>
          <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-4">Component Health</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {Object.entries(health.components ?? {}).map(([name, status]) => (
              <div key={name} className="flex items-center gap-3 bg-slate-900 border border-slate-800 rounded-lg p-3">
                <div className={cn(
                  "w-2 h-2 rounded-full shrink-0",
                  status === 'healthy' ? "bg-brand-green" :
                  status === 'degraded' ? "bg-brand-amber" : "bg-brand-red"
                )} />
                <div>
                  <div className="text-xs font-semibold text-slate-300 uppercase">{name}</div>
                  <div className={cn(
                    "text-xs",
                    status === 'healthy' ? "text-brand-green" :
                    status === 'degraded' ? "text-brand-amber" : "text-brand-red"
                  )}>{String(status)}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function PipelineStage({ name, count, status, icon: Icon }: any) {
  return (
    <div className="flex flex-col items-center gap-3 min-w-[80px]">
      <div className={cn(
        "w-12 h-12 rounded-xl flex items-center justify-center border shadow-sm transition-colors",
        status === 'success' ? "bg-slate-850 border-brand-cyan/30 text-brand-cyan" :
        status === 'warning' ? "bg-brand-amber/10 border-brand-amber/50 text-brand-amber" :
        "bg-slate-800 border-slate-700 text-slate-400"
      )}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="text-center">
        <div className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">{name}</div>
        <div className="text-xs font-mono text-slate-500 mt-1">{Number(count || 0).toLocaleString()}</div>
      </div>
    </div>
  );
}

function PipelineArrow() {
  return <ArrowRight className="w-5 h-5 text-slate-700 mx-2 shrink-0" />;
}

function MetricCard({ title, value, type = 'default', trend }: any) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardContent className="p-5">
        <h3 className="text-xs text-slate-400 uppercase tracking-wider mb-2">{title}</h3>
        <div className="flex items-end justify-between">
          <p className={cn(
            "text-2xl font-bold font-mono",
            type === 'default' ? "text-slate-100" :
            type === 'success' ? "text-brand-green" :
            type === 'warning' ? "text-brand-amber" : "text-red-400"
          )}>
            {Number(value || 0).toLocaleString()}
          </p>
          {trend && <span className="text-xs text-brand-green">{trend}</span>}
        </div>
      </CardContent>
    </Card>
  );
}

function DbIcon(props: any) {
  return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>;
}
function SearchIcon(props: any) {
  return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>;
}
