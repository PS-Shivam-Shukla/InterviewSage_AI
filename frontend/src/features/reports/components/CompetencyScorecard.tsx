import React from 'react';
import { BarChart2 } from 'lucide-react';
import { CompetencyScoreItem } from '../../../services/report.service';

interface CompetencyScorecardProps {
  scorecard: CompetencyScoreItem[];
}

export const CompetencyScorecard: React.FC<CompetencyScorecardProps> = ({ scorecard }) => {
  if (!scorecard || scorecard.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md">
        <h2 className="text-sm font-bold text-slate-100 mb-2">Competency Scorecard</h2>
        <p className="text-xs text-slate-400">No explicit competency metrics recorded for this session.</p>
      </div>
    );
  }

  const getBarColor = (score: number) => {
    if (score >= 80) return 'bg-emerald-500';
    if (score >= 70) return 'bg-indigo-500';
    if (score >= 60) return 'bg-amber-500';
    return 'bg-rose-500';
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center gap-2">
        <BarChart2 className="w-5 h-5 text-emerald-400" />
        <h2 className="text-base font-bold text-slate-100 font-display">Competency Breakdown</h2>
      </div>

      <div className="space-y-4">
        {scorecard.map((item, idx) => {
          const scoreVal = Math.round(item.score);
          const fullMark = item.fullMark || 100;
          const percentage = Math.min(100, Math.max(0, (scoreVal / fullMark) * 100));

          return (
            <div key={item.competency || idx} className="space-y-1.5">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-slate-200">{item.competency}</span>
                <span className="font-mono font-bold text-slate-100">
                  {scoreVal} / {fullMark}
                </span>
              </div>
              <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-2 rounded-full transition-all duration-500 ${getBarColor(percentage)}`}
                  style={{ width: `${percentage}%` }}
                  role="progressbar"
                  aria-valuenow={scoreVal}
                  aria-valuemin={0}
                  aria-valuemax={fullMark}
                  aria-label={item.competency}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
