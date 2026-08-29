import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useSourceContext } from '../contexts/SourceContext';
import { Server, Settings } from 'lucide-react';

export function SourceDetails() {
  const { currentSource } = useSourceContext();

  if (!currentSource) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="text-center text-slate-500">
          <Server className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Select a source from the top navigation to view details</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* HEADER */}
      <div className="flex items-start justify-between bg-slate-900 p-6 rounded-xl border border-slate-800">
        <div className="flex items-center gap-6">
           <div className="w-16 h-16 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700">
             <Server className="w-8 h-8 text-brand-cyan" />
           </div>
           <div>
             <div className="flex items-center gap-3 mb-1">
               <h1 className="text-2xl font-bold text-slate-100">{currentSource.name}</h1>
               <Badge variant="success" className="animate-pulse">Active</Badge>
             </div>
             <p className="text-slate-400 text-sm flex gap-4">
               <span><strong className="text-slate-300">ID:</strong> {currentSource.id}</span>
               <span><strong className="text-slate-300">Vendor:</strong> {currentSource.vendor}</span>
               <span><strong className="text-slate-300">Product:</strong> {currentSource.product}</span>
             </p>
           </div>
        </div>
        <div className="flex gap-2">
           <Button variant="outline"><Settings className="w-4 h-4 mr-2" /> Configure</Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* METRICS */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
             <CardTitle className="text-sm text-slate-400 uppercase">30-Day Volume</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="text-3xl font-mono text-slate-100 mb-2">14.2M</div>
             <div className="h-16 flex items-end gap-1 mb-2">
               {/* Sparkline placeholder */}
               {[3, 4, 2, 5, 4, 6, 8, 5, 7, 6, 9, 8, 12, 10, 8, 7, 5, 4, 3, 2, 4, 3, 5, 4, 3, 4, 2, 3, 4, 3].map((h, i) => (
                 <div key={i} className="flex-1 bg-brand-cyan/20 hover:bg-brand-cyan transition-colors rounded-t-sm" style={{ height: `${(h/12)*100}%` }} />
               ))}
             </div>
             <div className="flex justify-between text-xs text-slate-500">
               <span>30 days ago</span>
               <span>Today</span>
             </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
             <CardTitle className="text-sm text-slate-400 uppercase">Pipeline Efficiency</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="flex items-center justify-between mb-4">
               <div>
                 <div className="text-2xl font-mono text-brand-green">98.5%</div>
                 <div className="text-xs text-slate-500">Fast Path</div>
               </div>
               <div className="text-right">
                 <div className="text-2xl font-mono text-brand-purple">1.5%</div>
                 <div className="text-xs text-slate-500">Adaptive Path</div>
               </div>
             </div>
             <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden flex">
                <div className="bg-brand-green h-full" style={{ width: '98.5%' }} />
                <div className="bg-brand-purple h-full" style={{ width: '1.5%' }} />
             </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
             <CardTitle className="text-sm text-slate-400 uppercase">Integrity Score</CardTitle>
          </CardHeader>
          <CardContent>
             <div className="text-3xl font-mono text-slate-100 mb-1 flex items-baseline gap-2">
               99.9%
               <span className="text-sm text-brand-green">+0.1%</span>
             </div>
             <p className="text-sm text-slate-400 mb-4">Events passing schema validation</p>
             <div className="grid grid-cols-2 gap-2 text-xs">
               <div className="bg-slate-950 p-2 rounded border border-slate-800">
                 <div className="text-slate-500 mb-1">Dead Letters</div>
                 <div className="font-mono text-slate-300">2,104</div>
               </div>
               <div className="bg-slate-950 p-2 rounded border border-slate-800">
                 <div className="text-slate-500 mb-1">Drift Alerts</div>
                 <div className="font-mono text-slate-300">12</div>
               </div>
             </div>
          </CardContent>
        </Card>
      </div>

      {/* ACTIVE MAPPINGS */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-slate-100">Active Pipeline Topography</CardTitle>
          <Button variant="outline" size="sm">Create New Mapping</Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Template / Pattern</th>
                  <th className="p-3 font-medium">Target Schema</th>
                  <th className="p-3 font-medium">Fields Mapped</th>
                  <th className="p-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                <tr className="hover:bg-slate-800/50 transition-colors">
                  <td className="p-3"><Badge variant="success">Active</Badge></td>
                  <td className="p-3 font-mono text-xs text-brand-cyan">{"<14>1 %{TIMESTAMP_ISO8601} %{HOSTNAME} %{WORD} %{GREEDYDATA}"}</td>
                  <td className="p-3 text-slate-300">ECS Security v2</td>
                  <td className="p-3 text-slate-400">12 / 12 fields</td>
                  <td className="p-3 text-right space-x-2">
                    <Button variant="ghost" size="sm">Edit</Button>
                    <Button variant="ghost" size="sm">Test</Button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
