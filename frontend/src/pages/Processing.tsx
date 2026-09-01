import { useState, useEffect, useCallback } from 'react';
import { fetchStats, fetchOnboardingSessions, fetchHealth } from '../services/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Activity, Cpu, Database, Server, RefreshCw, Loader2 } from 'lucide-react';
import { cn } from '../utils/classnames';
import { formatIST } from '../utils/date';

export function Processing() {
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [statsData, healthData, sessData] = await Promise.allSettled([
        fetchStats(),
        fetchHealth(),
        fetchOnboardingSessions(),
      ]);

      if (statsData.status === 'fulfilled') setStats(statsData.value);
      if (healthData.status === 'fulfilled') setHealth(healthData.value);
      if (sessData.status === 'fulfilled') setSessions(sessData.value || []);
    } catch (e) {
      console.error('Failed to load processing telemetry:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 15000);
    return () => clearInterval(interval);
  }, [loadData]);

  const metrics = [
    {
      label: 'Worker Status',
      value: health?.components?.worker === 'healthy' ? 'Active (1 Node)' : 'Idle',
      icon: Cpu,
      color: 'text-brand-cyan',
    },
    {
      label: 'Ingested Events',
      value: (stats?.events_ingested ?? 0).toLocaleString(),
      icon: Activity,
      color: 'text-brand-purple',
    },
    {
      label: 'Normalized Events',
      value: (stats?.events_normalized ?? 0).toLocaleString(),
      icon: Database,
      color: 'text-brand-green',
    },
    {
      label: 'Dead Letters',
      value: (stats?.dead_letters ?? 0).toLocaleString(),
      icon: Server,
      color: stats?.dead_letters > 0 ? 'text-brand-red' : 'text-slate-400',
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Processing Engine & Sessions</h1>
          <p className="text-slate-400 mt-1">Monitor active ingestion sessions, pipelines, and worker throughput.</p>
        </div>
        <button
          onClick={loadData}
          className="flex items-center gap-2 px-3 py-1.5 bg-white hover:bg-slate-100 rounded-md border border-slate-300 text-sm font-bold text-slate-950 shadow-sm transition-all"
        >
          <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {metrics.map((m, i) => (
          <Card key={i} className="p-4 flex items-center gap-4 bg-slate-900 border-slate-800">
            <div className={`p-3 bg-slate-950 rounded-lg ${m.color}`}>
              <m.icon className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-100">{m.value}</div>
              <div className="text-xs text-slate-400">{m.label}</div>
            </div>
          </Card>
        ))}
      </div>

      <Card className="p-6 bg-slate-900 border-slate-800">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">
          Onboarding & Processing Sessions ({sessions.length})
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-medium">Session ID</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Current Stage</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Started</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                    Loading pipeline sessions...
                  </td>
                </tr>
              ) : sessions.length === 0 ? (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-500">
                    No active sessions found.
                  </td>
                </tr>
              ) : (
                sessions.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-4 py-3 font-mono text-xs text-brand-purple">{s.id ? `${s.id.slice(0, 16)}…` : '—'}</td>
                    <td className="px-4 py-3 font-mono text-xs text-slate-200">{s.source_id}</td>
                    <td className="px-4 py-3">
                      <Badge variant="secondary" className="font-mono text-[10px]">
                        {s.current_stage}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <Badge variant={s.status === 'COMPLETE' || s.status === 'READY' ? 'success' : s.status === 'FAILED' ? 'destructive' : 'warning'}>
                        {s.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-400 font-mono">
                      {formatIST(s.started_at, 'compact')}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
