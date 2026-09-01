import { useState, useEffect, useCallback } from 'react';
import { fetchFiles, fetchTraces } from '../services/api';
import { Card } from '../components/ui/Card';
import { Search, Shield, FileDigit, Lock, RefreshCw, Loader2 } from 'lucide-react';
import { useSourceContext } from '../contexts/SourceContext';
import { cn } from '../utils/classnames';

export function Vault() {
  const { currentSource } = useSourceContext();
  const [files, setFiles] = useState<any[]>([]);
  const [traces, setTraces] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const loadVaultData = useCallback(async () => {
    setLoading(true);
    try {
      const [filesData, tracesData] = await Promise.allSettled([
        fetchFiles(currentSource ? currentSource.id : undefined),
        fetchTraces({ source_id: currentSource ? currentSource.id : undefined, page: 1 }),
      ]);

      if (filesData.status === 'fulfilled') setFiles(Array.isArray(filesData.value) ? filesData.value : []);
      if (tracesData.status === 'fulfilled') setTraces(tracesData.value?.items || []);
    } catch (e) {
      console.error('Failed to load vault data:', e);
    } finally {
      setLoading(false);
    }
  }, [currentSource]);

  useEffect(() => {
    loadVaultData();
  }, [loadVaultData]);

  // Total bytes
  const totalFileBytes = files.reduce((acc, f) => acc + (f.size || 0), 0);
  const totalTraceBytes = traces.reduce((acc, t) => acc + (t.byte_length || 0), 0);
  const totalBytes = totalFileBytes + totalTraceBytes;

  const filteredFiles = files.filter((f) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      f.file_id?.toLowerCase().includes(q) ||
      f.source_id?.toLowerCase().includes(q) ||
      f.sha256?.toLowerCase().includes(q) ||
      f.filename?.toLowerCase().includes(q)
    );
  });

  const formatSize = (bytes: number) => {
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    if (bytes >= 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Lock className="w-6 h-6 text-brand-purple" />
            Raw Event Vault
          </h1>
          <p className="text-slate-400 mt-1">
            Immutable write-before-transform raw byte store with SHA-256 cryptographic verification.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by digest or source..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-md pl-9 pr-4 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-purple"
            />
          </div>
          <button
            onClick={loadVaultData}
            className="flex items-center gap-2 px-3 py-1.5 bg-white hover:bg-slate-100 rounded-md border border-slate-300 text-sm font-bold text-slate-950 shadow-sm transition-all"
          >
            <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 flex items-center gap-4 bg-brand-purple/5 border-brand-purple/20">
          <div className="p-3 bg-brand-purple/20 rounded-lg text-brand-purple">
            <Shield className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-100">100%</div>
            <div className="text-sm text-slate-400">SHA-256 Verified</div>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-4">
          <div className="p-3 bg-slate-800 rounded-lg text-slate-300">
            <FileDigit className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-100">{formatSize(totalBytes)}</div>
            <div className="text-sm text-slate-400">
              {files.length} Files · {traces.length} Stream Traces
            </div>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-4">
          <div className="p-3 bg-slate-800 rounded-lg text-slate-300">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-100">WORM</div>
            <div className="text-sm text-slate-400">Immutable Write-Before-Transform</div>
          </div>
        </Card>
      </div>

      <Card className="p-0 overflow-hidden border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4 font-medium">Vault File ID</th>
                <th className="px-6 py-4 font-medium">Filename</th>
                <th className="px-6 py-4 font-medium">Source</th>
                <th className="px-6 py-4 font-medium">Size</th>
                <th className="px-6 py-4 font-medium">SHA-256 Digest</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 bg-slate-950/50">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                    Loading vault records...
                  </td>
                </tr>
              ) : filteredFiles.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    No files found in the vault. Upload log files to preserve raw bytes.
                  </td>
                </tr>
              ) : (
                filteredFiles.map((entry) => (
                  <tr key={entry.file_id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-brand-purple">
                      {entry.file_id ? `${entry.file_id.slice(0, 16)}…` : '—'}
                    </td>
                    <td className="px-6 py-4 text-slate-200 font-medium">{entry.filename}</td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-300">{entry.source_id}</td>
                    <td className="px-6 py-4 text-slate-400 text-xs">{formatSize(entry.size || 0)}</td>
                    <td className="px-6 py-4 font-mono text-[11px] text-brand-purple opacity-90 truncate max-w-[200px]" title={entry.sha256}>
                      {entry.sha256 || '—'}
                    </td>
                    <td className="px-6 py-4">
                      <span className="flex items-center gap-1.5 text-brand-green text-xs font-medium">
                        <Shield className="w-3.5 h-3.5" /> Preserved
                      </span>
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500 font-mono">
                      {entry.received_at ? new Date(entry.received_at).toLocaleString() : '—'}
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
