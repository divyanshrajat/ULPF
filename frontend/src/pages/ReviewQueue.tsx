import { useState, useEffect } from 'react';
import { fetchQueue, API_BASE } from '../services/api';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { AlertTriangle, Filter, Search, ArrowRight, CornerDownRight, Zap, CheckCircle2 } from 'lucide-react';
import { ConfidenceBreakdown } from '../components/explainability/ConfidenceBreakdown';

export function ReviewQueue() {
  const [queue, setQueue] = useState<any[]>([]);
  const [activeReview, setActiveReview] = useState<any | null>(null);

  useEffect(() => {
    loadQueue();
  }, []);

  const loadQueue = () => {
    fetchQueue()
      .then(data => {
        setQueue(data);
        if (data.length > 0 && !activeReview) {
          setActiveReview(data[0]);
        }
      })
      .catch(console.error);
  };

  const handleApprove = async () => {
    if (!activeReview) return;
    const field_bindings: Record<string, string> = {};
    const confidence_summary: Record<string, number> = {};
    
    activeReview.proposals.forEach((p: any) => {
      field_bindings[p.source_field] = p.proposed_target;
      confidence_summary[p.source_field] = p.confidence;
    });

    try {
      const res = await fetch(`${API_BASE}/mappings/${activeReview.source_id}/${activeReview.template_id}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-ULPF-User': 'admin', 'X-ULPF-Role': 'admin' },
        body: JSON.stringify({ field_bindings, confidence_summary })
      });
      if (res.ok) {
        setActiveReview(null);
        loadQueue();
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleReject = async () => {
    if (!activeReview) return;
    try {
      const res = await fetch(`${API_BASE}/review/${activeReview.review_id}/reject`, { method: 'POST', headers: { 'X-ULPF-User': 'admin', 'X-ULPF-Role': 'admin' } });
      if (res.ok) {
        setActiveReview(null);
        loadQueue();
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6">
      {/* LEFT: QUEUE LIST */}
      <div className="w-1/3 flex flex-col gap-4 border-r border-slate-800 pr-6">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            Review Queue
            <Badge variant="warning">{queue.length}</Badge>
          </h2>
          <Button variant="ghost" size="icon"><Filter className="w-4 h-4" /></Button>
        </div>
        
        <div className="flex gap-2 text-sm border-b border-slate-800">
          <button className="px-3 py-2 text-brand-cyan border-b-2 border-brand-cyan">All</button>
          <button className="px-3 py-2 text-slate-400 hover:text-slate-200">High Risk</button>
          <button className="px-3 py-2 text-slate-400 hover:text-slate-200">Drift</button>
        </div>

        <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
          {queue.length === 0 && (
             <div className="text-center p-8 bg-slate-900 border border-slate-800 rounded-lg">
               <AlertTriangle className="w-8 h-8 text-slate-600 mx-auto mb-3" />
               <h3 className="text-slate-300 font-medium">No pending reviews</h3>
               <p className="text-slate-500 text-sm mt-1">All mappings have been validated.</p>
               <Button className="mt-4" variant="outline">View Approved Mappings</Button>
             </div>
          )}
          {queue.map((item) => (
            <Card 
              key={item.review_id}
              className={`cursor-pointer transition-colors ${activeReview?.review_id === item.review_id ? 'border-brand-cyan/50 bg-brand-cyan/5' : 'bg-slate-900 border-slate-800 hover:border-slate-600'}`}
              onClick={() => setActiveReview(item)}
            >
              <CardContent className="p-4">
                <div className="flex justify-between items-start mb-2">
                  <div className="text-xs font-semibold text-slate-400">{item.source_id}</div>
                  <Badge variant="warning" className="text-[10px] px-1.5 py-0">2 min ago</Badge>
                </div>
                <div className="text-sm font-mono text-slate-200 truncate mb-2" title={item.pattern}>{item.pattern}</div>
                <div className="flex items-center gap-4 text-xs text-slate-500">
                  <span className="flex items-center gap-1"><AlertTriangle className="w-3 h-3 text-brand-amber" /> {item.proposals?.length || 0} fields require review</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* RIGHT: REVIEW WORKSPACE */}
      {activeReview ? (
        <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
          <div className="flex items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800">
             <div>
               <h2 className="text-slate-100 font-bold">{activeReview.source_id}</h2>
               <p className="text-slate-400 text-sm">Reviewing {activeReview.proposals.length} AI mapping proposals</p>
             </div>
             <div className="flex gap-3">
                <Button variant="outline" onClick={handleReject}>Reject All</Button>
                <Button variant="default" onClick={handleApprove}>Approve Mapping</Button>
             </div>
          </div>

          <div className="space-y-4">
            {activeReview.proposals.map((p: any, i: number) => (
              <div key={i} className="grid grid-cols-3 gap-4 bg-slate-900 p-4 rounded-xl border border-slate-800">
                
                {/* 1. SOURCE EVIDENCE */}
                <div className="space-y-3 pr-4 border-r border-slate-800">
                  <div className="text-[10px] font-bold tracking-widest text-slate-500 uppercase">Source Evidence</div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Extracted Field</div>
                    <div className="font-mono text-sm text-slate-100 bg-slate-950 p-2 rounded border border-slate-800 inline-block">{p.source_field}</div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Inferred Type</div>
                    <Badge variant="secondary" className="font-mono">{p.source_type || 'STRING'}</Badge>
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Sample Value</div>
                    <div className="font-mono text-xs text-slate-300">"10.0.0.5"</div>
                  </div>
                </div>

                {/* 2. AI RECOMMENDATION */}
                <div className="space-y-3 pr-4 border-r border-slate-800">
                  <div className="text-[10px] font-bold tracking-widest text-brand-purple uppercase flex items-center gap-1">
                    <Zap className="w-3 h-3" /> AI Proposal
                  </div>
                  <div>
                    <div className="text-xs text-slate-400 mb-1">Target Canonical Field</div>
                    <div className="font-mono text-sm text-brand-cyan bg-brand-cyan/10 p-2 rounded border border-brand-cyan/20 inline-flex items-center gap-2">
                       <CornerDownRight className="w-4 h-4 text-brand-cyan/50" />
                       {p.proposed_target}
                    </div>
                  </div>
                  
                  <ConfidenceBreakdown 
                    confidence={p.confidence} 
                    decision={p.confidence >= 0.8 ? "AUTO_ACCEPT" : "REVIEW_REQUIRED"}
                    signals={{
                      name: p.confidence,
                      value: p.confidence > 0.5 ? p.confidence + 0.1 : 0.9,
                      context: 0.64,
                      history: 0.42
                    }}
                    className="mt-4"
                  />
                </div>

                {/* 3. HUMAN DECISION */}
                <div className="space-y-4">
                  <div className="text-[10px] font-bold tracking-widest text-brand-green uppercase">Human Decision</div>
                  <div className="space-y-2">
                    <Button variant="default" className="w-full justify-start text-brand-green bg-brand-green/10 border border-brand-green/30 hover:bg-brand-green/20">
                       <CheckCircle2 className="w-4 h-4 mr-2" /> Accept Proposal
                    </Button>
                    <Button variant="outline" className="w-full justify-start">
                       <Search className="w-4 h-4 mr-2 text-slate-400" /> Reassign Target
                    </Button>
                    <Button variant="outline" className="w-full justify-start border-brand-purple/30 text-brand-purple hover:bg-brand-purple/10">
                       <ArrowRight className="w-4 h-4 mr-2" /> Extension Only
                    </Button>
                  </div>
                </div>

              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex-1 flex items-center justify-center bg-slate-900 border border-slate-800 rounded-xl">
           <div className="text-center max-w-md">
             <CheckSquare className="w-12 h-12 text-slate-700 mx-auto mb-4" />
             <h2 className="text-xl font-bold text-slate-300 mb-2">Select a review item</h2>
             <p className="text-slate-500">Choose an item from the queue to review AI mapping proposals and provide human feedback.</p>
           </div>
        </div>
      )}
    </div>
  );
}

// Fallback icon if missing
function CheckSquare(props: any) { return <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg> }
