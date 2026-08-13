import React from 'react';
import { DollarSign, Cpu } from 'lucide-react';
import { CostAnalytics } from '../types/admin.types';

interface AICostBreakdownCardProps {
  costs?: CostAnalytics;
}

export const AICostBreakdownCard: React.FC<AICostBreakdownCardProps> = ({ costs }) => {
  if (!costs) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-emerald-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">AI Token & Model Cost Breakdown</h2>
        </div>
        <p className="text-xs text-slate-400">No AI usage cost analytics available.</p>
      </div>
    );
  }

  const today = costs.today_usd != null ? `$${costs.today_usd.toFixed(4)}` : '$0.0000';
  const week = costs.this_week_usd != null ? `$${costs.this_week_usd.toFixed(4)}` : '$0.0000';
  const month = costs.this_month_usd != null ? `$${costs.this_month_usd.toFixed(4)}` : '$0.0000';
  const totalTokens = costs.total_tokens_consumed ?? 0;

  const byModel = costs.by_model || {};

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <DollarSign className="h-5 w-5 text-emerald-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">
            AI Cost & Model Usage Analytics
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {totalTokens.toLocaleString()} Tokens Consumed
        </span>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">Today</span>
          <p className="text-lg font-bold text-slate-100 font-mono">{today}</p>
        </div>

        <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">This Week</span>
          <p className="text-lg font-bold text-slate-100 font-mono">{week}</p>
        </div>

        <div className="p-3.5 rounded-xl border border-slate-800 bg-slate-950/60 space-y-1">
          <span className="text-[11px] text-slate-400 uppercase font-semibold">This Month</span>
          <p className="text-lg font-bold text-emerald-400 font-mono">{month}</p>
        </div>
      </div>

      {Object.keys(byModel).length > 0 && (
        <div className="space-y-2 pt-2 border-t border-slate-800/60">
          <span className="text-xs font-semibold text-slate-400 flex items-center gap-1.5">
            <Cpu className="w-3.5 h-3.5 text-indigo-400" /> Model Cost Allocation
          </span>

          <div className="space-y-1.5">
            {Object.entries(byModel).map(([model, cost]) => (
              <div key={model} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950/40 border border-slate-800/60 text-xs">
                <span className="font-mono text-slate-200">{model}</span>
                <span className="font-mono font-bold text-emerald-400">${Number(cost).toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
