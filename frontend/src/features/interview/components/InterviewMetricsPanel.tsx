import React from 'react';
import { Activity, ShieldCheck, Cpu, MessageCircle, Clock, Zap } from 'lucide-react';
import { LiveInterviewMetrics } from '../types/interview.types';
import { formatSecondsToTimer } from '../utils/interviewHelpers';
import { cn } from '../../../lib/utils';

export interface InterviewMetricsPanelProps {
  metrics: LiveInterviewMetrics;
  className?: string;
}

export const InterviewMetricsPanel: React.FC<InterviewMetricsPanelProps> = ({
  metrics,
  className,
}) => {
  return (
    <div className={cn('p-6 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-5 shadow-xl', className)}>
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2 text-slate-200 font-bold text-sm uppercase tracking-wide">
          <Activity className="w-4 h-4 text-indigo-400" />
          <span>Live Session Analytics</span>
        </div>
        <span className="text-xs font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800/50 px-2.5 py-0.5 rounded-full flex items-center gap-1">
          <Zap className="w-3 h-3" />
          Live Telemetry
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Cpu className="w-3.5 h-3.5 text-emerald-400" />
            Technical Quality
          </span>
          <span className="text-xl font-bold font-mono text-emerald-400">
            {metrics.technicalScore}%
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <MessageCircle className="w-3.5 h-3.5 text-indigo-400" />
            Communication
          </span>
          <span className="text-xl font-bold font-mono text-indigo-400">
            {metrics.communicationScore}%
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
            Confidence Rating
          </span>
          <span className="text-xl font-bold font-mono text-amber-400">
            {metrics.confidenceScore}%
          </span>
        </div>

        <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col space-y-1">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            Time Elapsed
          </span>
          <span className="text-xl font-bold font-mono text-slate-200">
            {formatSecondsToTimer(metrics.timeElapsedSeconds || 0)}
          </span>
        </div>
      </div>

      <div className="pt-2 border-t border-slate-800/60 space-y-2">
        <div className="flex justify-between text-xs text-slate-400">
          <span>Target Competency</span>
          <span className="font-semibold text-indigo-300 text-right truncate max-w-[180px]">
            {metrics.currentCompetency || 'System Architecture'}
          </span>
        </div>
        <div className="flex justify-between text-xs text-slate-400">
          <span>Calculated Difficulty</span>
          <span className="font-semibold text-amber-300">
            {metrics.currentDifficulty || 'ADAPTIVE'}
          </span>
        </div>
      </div>
    </div>
  );
};
