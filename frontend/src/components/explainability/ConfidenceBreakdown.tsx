import { cn } from '../../utils/classnames';

interface ConfidenceBreakdownProps {
  confidence: number;
  signals?: {
    name: number;
    value: number;
    context: number;
    history: number;
  };
  decision: "AUTO_ACCEPT" | "REVIEW_REQUIRED" | "EXTENSION_ONLY";
  className?: string;
}

export function ConfidenceBreakdown({ confidence, signals, decision, className }: ConfidenceBreakdownProps) {
  const getDecisionColor = (decision: string) => {
    switch (decision) {
      case "AUTO_ACCEPT": return "text-brand-green border-brand-green/30 bg-brand-green/10";
      case "REVIEW_REQUIRED": return "text-brand-amber border-brand-amber/30 bg-brand-amber/10";
      case "EXTENSION_ONLY": return "text-brand-purple border-brand-purple/30 bg-brand-purple/10";
      default: return "text-slate-300";
    }
  };

  const getDecisionText = (decision: string) => {
    switch (decision) {
      case "AUTO_ACCEPT": return "✓ AUTO ACCEPT";
      case "REVIEW_REQUIRED": return "⚠ REVIEW REQUIRED";
      case "EXTENSION_ONLY": return "+ EXTENSION ONLY";
      default: return decision;
    }
  };

  return (
    <div className={cn("space-y-4", className)}>
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">Final Confidence</span>
        <span className="text-2xl font-bold text-slate-100">{(confidence * 100).toFixed(0)}%</span>
      </div>

      {signals && (
        <div className="space-y-2 mt-4 pt-4 border-t border-slate-800">
          <SignalBar label="Name similarity" value={signals.name} />
          <SignalBar label="Value compatibility" value={signals.value} />
          <SignalBar label="Context" value={signals.context} />
          <SignalBar label="History" value={signals.history} />
        </div>
      )}

      <div className={cn("mt-4 p-3 rounded border text-sm font-semibold flex items-center justify-center", getDecisionColor(decision))}>
        {getDecisionText(decision)}
      </div>
    </div>
  );
}

function SignalBar({ label, value }: { label: string, value: number }) {
  const percentage = Math.round(value * 100);
  return (
    <div className="flex flex-col gap-1">
      <div className="flex justify-between text-xs">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300 font-mono">{percentage}%</span>
      </div>
      <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden">
        <div 
          className="h-full bg-brand-purple transition-all duration-500 ease-out" 
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
