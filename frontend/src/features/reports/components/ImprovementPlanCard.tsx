import React from 'react';
import { Target, AlertTriangle } from 'lucide-react';
import { ImprovementPlanItem } from '../../../services/report.service';

interface ImprovementPlanCardProps {
  plan: ImprovementPlanItem[];
}

export const ImprovementPlanCard: React.FC<ImprovementPlanCardProps> = ({ plan }) => {
  if (!plan || plan.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-3">
        <div className="flex items-center gap-2 text-slate-400">
          <Target className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Targeted Improvement Plan</h2>
        </div>
        <p className="text-xs text-slate-400 leading-relaxed">
          No explicit improvement areas were recorded for this interview session. Great performance across evaluated competencies!
        </p>
      </div>
    );
  }

  const getPriorityBadge = (priority: string) => {
    const p = (priority || '').toLowerCase();
    if (p === 'high') {
      return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
    }
    if (p === 'medium') {
      return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
    }
    return 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400';
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center gap-2">
        <Target className="w-5 h-5 text-amber-400" />
        <h2 className="text-base font-bold text-slate-100 font-display">Targeted Improvement Plan & Recommendations</h2>
      </div>

      <div className="space-y-3">
        {plan.map((item, idx) => (
          <div
            key={item.id || idx}
            className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/60 space-y-2"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                <span className="font-semibold text-slate-100 text-sm">{item.topic}</span>
              </div>
              {item.priority && (
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getPriorityBadge(item.priority)}`}>
                  {item.priority} Priority
                </span>
              )}
            </div>

            <p className="text-xs text-slate-300 leading-relaxed pl-6">
              {item.description}
            </p>

            {item.targetSkill && (
              <div className="pl-6 pt-1">
                <span className="text-[11px] font-medium text-slate-400">
                  Target Skill Area:{' '}
                  <span className="text-indigo-300 font-semibold">{item.targetSkill}</span>
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
