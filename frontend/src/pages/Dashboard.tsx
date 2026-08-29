import { useState, useEffect } from 'react';
import { fetchStats } from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { ArrowRight, GitCommit, FileText, CheckCircle2, AlertTriangle, Zap, Network } from 'lucide-react';
import { cn } from '../utils/classnames';

export function Dashboard() {
  const [stats, setStats] = useState({ events_ingested: 0, events_normalized: 0, review_queue: 0, dead_letters: 0 });

  useEffect(() => {
    fetchStats()
      .then(data => setStats(data))
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-8 max-w-6xl mx-auto pb-12">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-2">ULPF PIPELINE</h1>
          <p className="text-slate-400">Adaptive preprocessing for heterogeneous logs</p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <Badge variant="success" className="gap-1.5"><div className="w-1.5 h-1.5 rounded-full bg-brand-green animate-pulse" /> Operational</Badge>
          <span className="text-xs text-slate-500 font-mono">v2.4.1-alpha</span>
        </div>
      </div>

      {/* PIPELINE VISUALIZATION */}
      <section>
        <h2 className="text-sm font-semibold text-slate-500 uppercase tracking-widest mb-4">Pipeline Overview</h2>
        <div className="flex items-center justify-between bg-slate-900 border border-slate-800 rounded-xl p-6 overflow-x-auto">
          <PipelineStage name="INGEST" count={stats.events_ingested} status="success" icon={FileText} />
          <PipelineArrow />
          <PipelineStage name="PRESERVE" count={stats.events_ingested} status="success" icon={Database} />
          <PipelineArrow />
          <PipelineStage name="DETECT" count={stats.events_ingested} status="success" icon={Search} />
          <PipelineArrow />
          <PipelineStage name="DISCOVER" count={142} status="success" icon={Zap} />
          <PipelineArrow />
          <PipelineStage name="MAP" count={142} status="success" icon={Network} />
          <PipelineArrow />
          <PipelineStage name="REVIEW" count={stats.review_queue} status={stats.review_queue > 0 ? "warning" : "success"} icon={AlertTriangle} />
          <PipelineArrow />
          <PipelineStage name="NORMALIZE" count={stats.events_normalized} status="success" icon={CheckCircle2} />
          <PipelineArrow />
          <PipelineStage name="TRACE" count={stats.events_normalized} status="success" icon={GitCommit} />
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
            <div className="text-4xl font-mono text-slate-100 mb-2">142</div>
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
            <div className="text-4xl font-mono text-slate-100 mb-2">{stats.events_normalized - 142 > 0 ? stats.events_normalized - 142 : 0}</div>
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
        <div className="grid grid-cols-4 gap-4">
          <MetricCard title="Ingested" value={stats.events_ingested} />
          <MetricCard title="Normalized" value={stats.events_normalized} trend="+12%" />
          <MetricCard title="Drift Events" value={23} type="warning" />
          <MetricCard title="Integrity Failures" value={stats.dead_letters} type={stats.dead_letters > 0 ? "error" : "success"} />
        </div>
      </section>
    </div>
  );
}

function PipelineStage({ name, count, status, icon: Icon }: any) {
  return (
    <div className="flex flex-col items-center gap-3 min-w-[80px]">
      <div className={cn(
        "w-12 h-12 rounded-xl flex items-center justify-center border shadow-sm transition-colors cursor-pointer hover:bg-slate-800",
        status === 'success' ? "bg-slate-850 border-brand-cyan/30 text-brand-cyan" : 
        status === 'warning' ? "bg-brand-amber/10 border-brand-amber/50 text-brand-amber" : 
        "bg-slate-800 border-slate-700 text-slate-400"
      )}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="text-center">
        <div className="text-[10px] font-bold text-slate-300 uppercase tracking-wider">{name}</div>
        <div className="text-xs font-mono text-slate-500 mt-1">{count.toLocaleString()}</div>
      </div>
    </div>
  );
}

function PipelineArrow() {
  return <ArrowRight className="w-5 h-5 text-slate-700 mx-2 shrink-0" />;
}

function MetricCard({ title, value, type = "default", trend }: any) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardContent className="p-5">
        <h3 className="text-xs text-slate-400 uppercase tracking-wider mb-2">{title}</h3>
        <div className="flex items-end justify-between">
          <p className={cn(
            "text-2xl font-bold font-mono",
            type === "default" ? "text-slate-100" :
            type === "success" ? "text-brand-green" :
            type === "warning" ? "text-brand-amber" : "text-brand-red"
          )}>
            {value.toLocaleString()}
          </p>
          {trend && <span className="text-xs text-brand-green">{trend}</span>}
        </div>
      </CardContent>
    </Card>
  );
}

// Temporary missing icons fallback until we import them properly at top
function Database(props: any) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg> }
function Search(props: any) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg> }
