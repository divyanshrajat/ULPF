import { Card } from '../components/ui/Card';
import { Search, Shield, FileDigit, Download, Lock } from 'lucide-react';

export function Vault() {
  const vaultEntries = [
    { id: 'VLT-8921-001', source: 'Firewall-X', timestamp: '2026-08-29T10:15:00Z', size: '1.2 KB', digest: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', status: 'Verified' },
    { id: 'VLT-8921-002', source: 'Firewall-X', timestamp: '2026-08-29T10:15:01Z', size: '0.8 KB', digest: '8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92', status: 'Verified' },
    { id: 'VLT-8921-003', source: 'Windows-DC', timestamp: '2026-08-29T10:15:05Z', size: '2.4 KB', digest: 'c7be1ed902fb8de4d17f41bf39546059c03b1ab48fae42013f9822a101f37eeb', status: 'Verified' },
    { id: 'VLT-8921-004', source: 'Okta-Auth', timestamp: '2026-08-29T10:15:10Z', size: '1.1 KB', digest: '315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3', status: 'Verified' },
    { id: 'VLT-8921-005', source: 'Firewall-X', timestamp: '2026-08-29T10:15:15Z', size: '1.5 KB', digest: '52b855e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b78', status: 'Verified' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Lock className="w-6 h-6 text-brand-purple" />
            Raw Event Vault
          </h1>
          <p className="text-slate-400 mt-1">Immutable storage for byte-for-byte original payloads with SHA-256 integrity verification.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input 
              type="text" 
              placeholder="Search by digest or source..." 
              className="bg-slate-900 border border-slate-800 rounded-md pl-9 pr-4 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-purple"
            />
          </div>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 text-sm font-medium text-slate-200 transition-colors">
            <Download className="w-4 h-4" />
            Export Audit Log
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
            <div className="text-sm text-slate-400">Integrity Verified</div>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-4">
          <div className="p-3 bg-slate-800 rounded-lg text-slate-300">
            <FileDigit className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-100">1.2 TB</div>
            <div className="text-sm text-slate-400">Total Vault Size</div>
          </div>
        </Card>
        <Card className="p-4 flex items-center gap-4">
          <div className="p-3 bg-slate-800 rounded-lg text-slate-300">
            <Lock className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-100">Immutable</div>
            <div className="text-sm text-slate-400">Storage Policy</div>
          </div>
        </Card>
      </div>

      <Card className="p-0 overflow-hidden border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4 font-medium">Vault ID</th>
                <th className="px-6 py-4 font-medium">Timestamp</th>
                <th className="px-6 py-4 font-medium">Source</th>
                <th className="px-6 py-4 font-medium">Size</th>
                <th className="px-6 py-4 font-medium">SHA-256 Digest</th>
                <th className="px-6 py-4 font-medium">Integrity</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50 bg-slate-950/50">
              {vaultEntries.map((entry) => (
                <tr key={entry.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-slate-400">{entry.id}</td>
                  <td className="px-6 py-4 text-slate-300">{entry.timestamp}</td>
                  <td className="px-6 py-4 font-medium text-slate-200">{entry.source}</td>
                  <td className="px-6 py-4 text-slate-400">{entry.size}</td>
                  <td className="px-6 py-4 font-mono text-xs text-brand-purple opacity-80">{entry.digest}</td>
                  <td className="px-6 py-4">
                    <span className="flex items-center gap-1.5 text-brand-green text-xs font-medium">
                      <Shield className="w-3.5 h-3.5" /> {entry.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
