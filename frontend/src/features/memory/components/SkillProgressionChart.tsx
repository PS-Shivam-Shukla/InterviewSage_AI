import React from 'react';
import { TrendingUp, TrendingDown, Minus, Layers } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from 'recharts';
import { SkillProgress } from '../types/memory.types';
import { AccessibleDataTable } from '../../../components/ui/AccessibleDataTable';

interface SkillProgressionChartProps {
  skills?: SkillProgress[];
}

export const SkillProgressionChart: React.FC<SkillProgressionChartProps> = ({ skills }) => {
  if (!skills || skills.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <Layers className="h-5 w-5 text-indigo-400" aria-hidden="true" />
          <h2 className="text-base font-bold text-slate-100 font-display">Longitudinal Skill Progression</h2>
        </div>
        <div className="py-12 text-center space-y-2">
          <Layers className="w-8 h-8 text-slate-600 mx-auto" aria-hidden="true" />
          <p className="text-xs text-slate-400">
            No skill progression data recorded yet. Complete interview evaluations to track skill scores over time.
          </p>
        </div>
      </div>
    );
  }

  const chartData = skills.map((s) => ({
    name: s.skill_name,
    Current: Math.round(s.current_score),
    Best: Math.round(s.best_score),
    Average: Math.round(s.average_score),
    trend: s.trend,
  }));

  const tableHeaders = ['Skill', 'Current Score (%)', 'Best Score (%)', 'Average Score (%)', 'Trend'];
  const tableRows = chartData.map((d) => [d.name, `${d.Current}%`, `${d.Best}%`, `${d.Average}%`, d.trend]);

  const getTrendBadge = (trend: string) => {
    const t = (trend || '').toUpperCase();
    if (t === 'IMPROVING') {
      return (
        <span className="inline-flex items-center gap-1 text-xs font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/30">
          <TrendingUp className="w-3 h-3" aria-hidden="true" /> Improving
        </span>
      );
    }
    if (t === 'REGRESSING') {
      return (
        <span className="inline-flex items-center gap-1 text-xs font-bold text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/30">
          <TrendingDown className="w-3 h-3" aria-hidden="true" /> Regressing
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 text-xs font-bold text-slate-400 bg-slate-800 px-2 py-0.5 rounded-full border border-slate-700">
        <Minus className="w-3 h-3" aria-hidden="true" /> Stable
      </span>
    );
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-6">
      <AccessibleDataTable
        caption="Longitudinal Skill Progression Data"
        headers={tableHeaders}
        rows={tableRows}
      />

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="h-5 w-5 text-indigo-400" aria-hidden="true" />
          <h2 className="text-base font-bold text-slate-100 font-display">
            Longitudinal Skill Progression
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">{skills.length} Evaluated Skills</span>
      </div>

      {/* Recharts Skill Scores Bar Chart */}
      <div className="h-72 w-full" aria-label="Skill progression bar chart graph">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis
              dataKey="name"
              stroke="#94a3b8"
              fontSize={11}
              tickLine={false}
              interval={0}
              angle={-45}
              textAnchor="end"
              height={65}
              tickFormatter={(val: string) => (val && val.length > 18 ? `${val.substring(0, 16)}...` : val)}
            />
            <YAxis domain={[0, 100]} stroke="#64748b" fontSize={11} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                borderColor: '#334155',
                borderRadius: '0.75rem',
                color: '#f8fafc',
                fontSize: '12px',
              }}
            />
            <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
            <Bar dataKey="Current" fill="#6366f1" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Best" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Average" fill="#f59e0b" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Skill List with Trend Indicators */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 pt-2 border-t border-slate-800/60">
        {skills.map((item) => (
          <div key={item.id || item.skill_name} className="p-3 rounded-xl border border-slate-800 bg-slate-950/60 flex items-center justify-between">
            <div>
              <span className="font-semibold text-slate-200 text-xs">{item.skill_name}</span>
              <p className="text-[11px] text-slate-400 font-mono">
                Current: {Math.round(item.current_score)}% · Best: {Math.round(item.best_score)}%
              </p>
            </div>
            {getTrendBadge(item.trend)}
          </div>
        ))}
      </div>
    </div>
  );
};
