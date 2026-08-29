import React from 'react';
import { CheckCircle2, ArrowRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/Card';

interface TimelineEvent {
  description: React.ReactNode;
  status: "success" | "warning" | "error" | "info";
}

interface WhatHappenedProps {
  events: TimelineEvent[];
}

export function WhatHappened({ events }: WhatHappenedProps) {
  return (
    <Card className="bg-slate-900 border-slate-800">
      <CardHeader className="pb-3 border-b border-slate-800/50">
        <CardTitle className="text-sm text-slate-300 flex items-center gap-2">
          WHAT HAPPENED?
        </CardTitle>
      </CardHeader>
      <CardContent className="pt-4">
        <div className="space-y-4 relative before:absolute before:inset-0 before:ml-2 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-800 before:to-transparent">
          {events.map((event, index) => (
            <div key={index} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active">
              <div className="flex items-center justify-center w-5 h-5 rounded-full border border-slate-700 bg-slate-900 text-slate-500 shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2 shadow">
                {event.status === 'success' && <CheckCircle2 className="w-3 h-3 text-brand-cyan" />}
                {event.status === 'warning' && <div className="w-2 h-2 rounded-full bg-brand-amber" />}
                {event.status === 'error' && <div className="w-2 h-2 rounded-full bg-brand-red" />}
                {event.status === 'info' && <ArrowRight className="w-3 h-3 text-slate-400" />}
              </div>
              <div className="w-[calc(100%-2.5rem)] md:w-[calc(50%-1.25rem)] px-4 py-3 rounded border border-slate-800 bg-slate-800/20 text-sm text-slate-300">
                {event.description}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
