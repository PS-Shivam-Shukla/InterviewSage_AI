import React from 'react';
import { Radio, Users, Clock, Bot, Cpu } from 'lucide-react';
import { LiveInterviewItem } from '../types/admin.types';

interface LiveInterviewsMonitorProps {
  liveSessions?: LiveInterviewItem[];
}

export const LiveInterviewsMonitor: React.FC<LiveInterviewsMonitorProps> = ({ liveSessions }) => {
  if (!liveSessions || liveSessions.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <Radio className="h-5 w-5 text-emerald-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Live Interview Operations Monitor</h2>
        </div>
        <div className="py-8 text-center space-y-2">
          <Users className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-xs text-slate-400">
            No candidate interview sessions currently active in real-time.
          </p>
        </div>
      </div>
    );
  }

  const formatElapsed = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Radio className="h-5 w-5 text-emerald-400 animate-pulse" />
          <h2 className="text-base font-bold text-slate-100 font-display">Active Live Interview Sessions</h2>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-500/10 border border-emerald-500/30 text-emerald-400">
          {liveSessions.length} Live Sessions
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950/60 text-slate-400 font-semibold border-b border-slate-800">
            <tr>
              <th className="py-3 px-4">Candidate</th>
              <th className="py-3 px-4">Round / Stage</th>
              <th className="py-3 px-4">Q#</th>
              <th className="py-3 px-4">Active Agent</th>
              <th className="py-3 px-4">Elapsed</th>
              <th className="py-3 px-4">Worker</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {liveSessions.map((item) => (
              <tr key={item.interview_id} className="hover:bg-slate-900/40 transition-colors">
                <td className="py-3 px-4 font-semibold text-slate-100 whitespace-nowrap">
                  {item.candidate_name}
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <span className="px-2 py-0.5 rounded text-[11px] bg-slate-800 border border-slate-700 text-slate-200">
                    {item.current_round} · {item.workflow_stage}
                  </span>
                </td>
                <td className="py-3 px-4 font-mono text-slate-300 whitespace-nowrap">
                  Q{item.question_number}
                </td>
                <td className="py-3 px-4 whitespace-nowrap">
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono text-indigo-400">
                    <Bot className="w-3.5 h-3.5" />
                    {item.current_agent}
                  </span>
                </td>
                <td className="py-3 px-4 font-mono text-slate-400 whitespace-nowrap">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-500" />
                    {formatElapsed(item.elapsed_seconds)}
                  </div>
                </td>
                <td className="py-3 px-4 font-mono text-slate-500 whitespace-nowrap">
                  <div className="flex items-center gap-1 text-[11px]">
                    <Cpu className="w-3 h-3 text-slate-600" />
                    {item.worker_id}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
