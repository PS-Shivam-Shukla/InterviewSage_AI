import React from 'react';
import { Target, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface ImprovementInsightsCardProps {
  weakCompetencies?: string[];
}

export const ImprovementInsightsCard: React.FC<ImprovementInsightsCardProps> = ({ weakCompetencies }) => {
  if (!weakCompetencies || weakCompetencies.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-3">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Targeted Focus & Skill Recommendations</h2>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-xs text-emerald-300">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>No critical weak competencies detected across your evaluated sessions. Keep up the high performance!</span>
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center gap-2 text-amber-400">
        <AlertTriangle className="w-5 h-5" />
        <h2 className="text-base font-bold text-slate-100 font-display">Recommended Areas for Focused Improvement</h2>
      </div>

      <p className="text-xs text-slate-400 leading-relaxed">
        The EvaluationAgent has flagged the following competency areas where average scores fell below benchmark targets:
      </p>

      <div className="flex flex-wrap gap-2 pt-1">
        {weakCompetencies.map((comp) => (
          <div
            key={comp}
            className="flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3.5 py-2 text-xs font-semibold text-amber-300 shadow-sm"
          >
            <Target className="w-3.5 h-3.5 text-amber-400" />
            <span>{comp}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
