import { useState, useEffect, useCallback } from 'react';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import {
  Settings, HardDrive, Cpu, AlertTriangle, Key,
  RefreshCw, Loader2, ShieldCheck, CheckCircle2, XCircle,
} from 'lucide-react';
import { fetchHealth, fetchAirgapStatus, fetchSystemConfig } from '../services/api';
import { cn } from '../utils/classnames';

export function System() {
  const [retention, setRetention] = useState('90');
  const [fastPath, setFastPath] = useState(true);

  const [health, setHealth] = useState<any>(null);
  const [airgap, setAirgap] = useState<any>(null);
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSystemInfo = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [healthData, airgapData, configData] = await Promise.allSettled([
        fetchHealth(),
        fetchAirgapStatus(),
        fetchSystemConfig().catch(() => null),
      ]);

      if (healthData.status === 'fulfilled') setHealth(healthData.value);
      if (airgapData.status === 'fulfilled') setAirgap(airgapData.value);
      if (configData.status === 'fulfilled') setConfig(configData.value);
    } catch (e: any) {
      setError(e?.message || 'Failed to load system details');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSystemInfo();
  }, [loadSystemInfo]);

  const mode = airgap?.mode || health?.mode || 'internet';
  const isAirgap = mode === 'airgap';

  return (
    <div className="space-y-6 max-w-5xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Settings className="w-6 h-6 text-brand-cyan" />
            System Configuration & Runtime
          </h1>
          <p className="text-slate-400 mt-1">
            Manage global middleware settings, runtime air-gap enforcement, and component statuses.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant={isAirgap ? 'warning' : 'success'} className="px-3 py-1 text-xs">
            {isAirgap ? 'AIR-GAPPED MODE' : 'INTERNET MODE'}
          </Badge>
          <Button variant="outline" size="sm" onClick={loadSystemInfo} disabled={loading}>
            <RefreshCw className={cn('w-4 h-4 mr-2', loading && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-brand-red/10 border border-brand-red/30 rounded-xl text-brand-red text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {error}
        </div>
      )}

      {/* AIR-GAP COMPLIANCE BANNER */}
      <Card className={cn(
        "p-6 border",
        isAirgap ? "bg-brand-amber/5 border-brand-amber/30" : "bg-slate-900 border-slate-800"
      )}>
        <div className="flex items-start gap-4">
          <div className={cn(
            "p-3 rounded-lg",
            isAirgap ? "bg-brand-amber/20 text-brand-amber" : "bg-brand-cyan/10 text-brand-cyan"
          )}>
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div className="flex-1">
            <div className="flex items-center justify-between mb-1">
              <h2 className="text-base font-bold text-slate-100">
                Air-Gap Verification & Policy: {airgap?.network_policy || (isAirgap ? 'STRICT_OFFLINE' : 'INTERNET_ALLOWED')}
              </h2>
              <Badge variant={airgap?.outbound_dependencies === false ? 'success' : 'secondary'}>
                {airgap?.outbound_dependencies === false ? '0 Outbound Calls' : 'Online Runtime'}
              </Badge>
            </div>
            <p className="text-xs text-slate-400 mb-4">
              {isAirgap
                ? 'Strict air-gap compliance active. All AI embeddings, models, and dependencies run strictly on local memory.'
                : 'Connected deployment active. Online model download available.'}
            </p>

            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">Local Model:</span>
                <span className="font-mono text-brand-cyan">{config?.model_path || 'all-MiniLM-L6-v2'}</span>
              </div>
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">Raw Vault Dir:</span>
                <span className="font-mono text-brand-purple">{config?.vault_dir || '/data/vault'}</span>
              </div>
              <div className="p-3 bg-slate-950/80 rounded border border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">OpenSearch Index:</span>
                <span className="font-mono text-slate-200">{config?.opensearch_index || 'ulpf-events'}</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Core Processing Engine */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <Cpu className="w-5 h-5 text-brand-cyan" />
            <h2 className="text-lg font-semibold text-slate-100">Processing Engine & Thresholds</h2>
          </div>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-slate-200 font-medium text-sm">Deterministic Fast Path</div>
                <div className="text-xs text-slate-400">Bypass AI inference for active templates</div>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={fastPath}
                  onChange={() => setFastPath(!fastPath)}
                />
                <div className="w-11 h-6 bg-slate-700 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-brand-cyan" />
              </label>
            </div>

            <div className="p-3 bg-slate-950 rounded border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-400">Review Floor Threshold:</span>
                <span className="font-mono text-brand-amber">{config?.thresholds?.mapping_review_floor ?? 0.65}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Auto-Accept Threshold:</span>
                <span className="font-mono text-brand-green">{config?.thresholds?.mapping_auto_accept ?? 0.90}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Drain3 Tree Depth / Sim:</span>
                <span className="font-mono text-slate-300">
                  {config?.drain3?.depth ?? 4} / {config?.drain3?.sim_th ?? 0.4}
                </span>
              </div>
            </div>
          </div>
        </Card>

        {/* Component Health Grid */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <HardDrive className="w-5 h-5 text-brand-purple" />
            <h2 className="text-lg font-semibold text-slate-100">Live Component Status</h2>
          </div>

          <div className="space-y-3">
            {health?.components ? (
              Object.entries(health.components).map(([name, status]) => {
                let note = '';
                if (name === 'opensearch' && status !== 'healthy') {
                  note = 'Port 9200 offline. Operating in local WORM Vault & DB mode (zero data loss)';
                } else if (name === 'redis' && status !== 'healthy') {
                  note = 'In-memory async queue active';
                } else if (name === 'model' && status === 'healthy') {
                  note = 'SentenceTransformers MiniLM active';
                } else if (name === 'vault' && status === 'healthy') {
                  note = 'Write-before-transform SHA-256 storage active';
                }

                return (
                  <div
                    key={name}
                    className="p-2.5 bg-slate-950 rounded border border-slate-800 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-300 uppercase">{name}</span>
                      <div className="flex items-center gap-1.5">
                        {status === 'healthy' ? (
                          <CheckCircle2 className="w-3.5 h-3.5 text-brand-green" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 text-brand-amber" />
                        )}
                        <span
                          className={cn(
                            'font-mono uppercase font-semibold',
                            status === 'healthy' ? 'text-brand-green' : 'text-brand-amber'
                          )}
                        >
                          {String(status)}
                        </span>
                      </div>
                    </div>
                    {note && (
                      <div className="text-[11px] text-slate-500 flex items-center gap-1">
                        <span>ℹ️</span> {note}
                      </div>
                    )}
                  </div>
                );
              })
            ) : (
              <div className="text-center py-6 text-slate-500 text-sm">
                <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                Querying component health...
              </div>
            )}
          </div>
        </Card>

        {/* Data Retention & Storage */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <HardDrive className="w-5 h-5 text-brand-purple" />
            <h2 className="text-lg font-semibold text-slate-100">Storage & Retention</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-slate-200 font-medium mb-1 text-sm">Raw Vault Retention</label>
              <div className="text-xs text-slate-400 mb-2">Duration to keep original immutable payloads.</div>
              <select
                value={retention}
                onChange={(e) => setRetention(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-md px-3 py-2 text-slate-200 text-sm focus:outline-none focus:ring-1 focus:ring-brand-purple"
              >
                <option value="30">30 Days</option>
                <option value="90">90 Days (Default)</option>
                <option value="180">180 Days</option>
                <option value="365">1 Year</option>
                <option value="forever">Indefinite (Statutory WORM)</option>
              </select>
            </div>
          </div>
        </Card>

        {/* Access & Security */}
        <Card className="p-6 space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
            <Key className="w-5 h-5 text-brand-green" />
            <h2 className="text-lg font-semibold text-slate-100">API & Authentication</h2>
          </div>

          <div className="space-y-4">
            <div className="p-3 bg-slate-950 rounded border border-slate-800 text-xs space-y-2">
              <div className="flex justify-between">
                <span className="text-slate-400">Auth Method:</span>
                <span className="font-mono text-brand-green">HTTP Basic + RBAC</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Active Roles:</span>
                <span className="font-mono text-slate-300">viewer | approver | administrator</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">API Prefix:</span>
                <span className="font-mono text-brand-cyan">{config?.api_prefix || '/api/v1'}</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
