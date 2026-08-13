import React from 'react';
import { Award, TrendingUp } from 'lucide-react';

interface OverallScoreCardProps {
  score: number;
}

export const OverallScoreCard: React.FC<OverallScoreCardProps> = ({ score }) => {
  const roundedScore = Math.round(score);

  const getPerformanceLabel = (val: number) => {
    if (val >= 85) return { label: 'Outstanding Performance', color: 'text-emerald-400', badgeBg: 'bg-emerald-500/10 border-emerald-500/30' };
    if (val >= 75) return { label: 'Strong Performance', color: 'text-indigo-400', badgeBg: 'bg-indigo-500/10 border-indigo-500/30' };
    if (val >= 60) return { label: 'Good Progress', color: 'text-amber-400', badgeBg: 'bg-amber-500/10 border-amber-500/30' };
    return { label: 'Needs Improvement', color: 'text-rose-400', badgeBg: 'bg-rose-500/10 border-rose-500/30' };
  };

  const { label, color, badgeBg } = getPerformanceLabel(roundedScore);

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md">
      <div className="flex items-center justify-between text-slate-400 mb-4">
        <span className="text-xs font-semibold uppercase tracking-wider">Overall AI Evaluation Score</span>
        <Award className="w-5 h-5 text-indigo-400" />
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
        <div className="flex items-baseline gap-3">
          <span className="text-5xl font-extrabold text-slate-100 font-mono tracking-tight">
            {roundedScore}
          </span>
          <span className="text-xl font-medium text-slate-500 font-mono">
            / 100
          </span>
        </div>

        <div className="space-y-1 sm:text-right">
          <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${badgeBg} ${color}`}>
            <TrendingUp className="w-3.5 h-3.5" />
            <span>{label}</span>
          </div>
          <p className="text-xs text-slate-400">
            Calculated across technical rigor, problem solving & communication.
          </p>
        </div>
      </div>
    </div>
  );
};
