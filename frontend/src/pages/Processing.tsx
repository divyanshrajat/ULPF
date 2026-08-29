import { Card } from '../components/ui/Card';
import { Activity, Cpu, Database, Server } from 'lucide-react';

export function Processing() {
  const metrics = [
    { label: 'Active Workers', value: '4', icon: Cpu, color: 'text-brand-cyan' },
    { label: 'Events/sec', value: '1,240', icon: Activity, color: 'text-brand-purple' },
    { label: 'Queue Size', value: '0', icon: Database, color: 'text-brand-green' },
    { label: 'Uptime', value: '99.9%', icon: Server, color: 'text-slate-400' },
  ];

  const jobs = [
    { id: 'JOB-9821', source: 'Firewall-X', status: 'Processing', progress: 45, items: '4,500 / 10,000' },
    { id: 'JOB-9820', source: 'Windows-DC', status: 'Completed', progress: 100, items: '2,104 / 2,104' },
    { id: 'JOB-9819', source: 'Okta-Auth', status: 'Completed', progress: 100, items: '850 / 850' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Processing Engine</h1>
          <p className="text-slate-400 mt-1">Monitor active ingestion pipelines and worker node health.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {metrics.map((m, i) => (
          <Card key={i} className="p-4 flex items-center gap-4">
            <div className={`p-3 bg-slate-900 rounded-lg ${m.color}`}>
              <m.icon className="w-6 h-6" />
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-100">{m.value}</div>
              <div className="text-sm text-slate-400">{m.label}</div>
            </div>
          </Card>
        ))}
      </div>

      <Card className="p-6">
        <h3 className="text-lg font-semibold text-slate-100 mb-4">Active & Recent Jobs</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-4 py-3 font-medium">Job ID</th>
                <th className="px-4 py-3 font-medium">Source</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Progress</th>
                <th className="px-4 py-3 font-medium">Items</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {jobs.map((job) => (
                <tr key={job.id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-4 py-3 font-mono text-xs">{job.id}</td>
                  <td className="px-4 py-3">{job.source}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      job.status === 'Completed' ? 'bg-brand-green/10 text-brand-green' : 'bg-brand-cyan/10 text-brand-cyan'
                    }`}>
                      {job.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-full bg-slate-800 rounded-full h-1.5 max-w-[100px]">
                        <div 
                          className={`h-1.5 rounded-full ${job.status === 'Completed' ? 'bg-brand-green' : 'bg-brand-cyan'}`}
                          style={{ width: `${job.progress}%` }}
                        ></div>
                      </div>
                      <span className="text-xs text-slate-400">{job.progress}%</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-slate-400">{job.items}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
