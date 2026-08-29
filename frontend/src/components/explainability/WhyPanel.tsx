import { HelpCircle } from 'lucide-react';
import { cn } from '../../utils/classnames';
import { Card, CardContent } from '../ui/Card';

interface WhyPanelProps {
  title?: string;
  reasons: string[];
  className?: string;
}

export function WhyPanel({ title = "WHY?", reasons, className }: WhyPanelProps) {
  return (
    <Card className={cn("bg-slate-800/50 border-slate-700/50", className)}>
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <HelpCircle className="w-4 h-4 text-brand-purple" />
          <h4 className="text-xs font-bold text-slate-300 tracking-wider uppercase">{title}</h4>
        </div>
        <ul className="space-y-2">
          {reasons.map((reason, idx) => (
            <li key={idx} className="text-sm text-slate-300 flex items-start gap-2 leading-relaxed">
              <span className="text-brand-purple/50 mt-1">"</span>
              <span className="italic text-slate-400">{reason}</span>
              <span className="text-brand-purple/50 mt-1">"</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
