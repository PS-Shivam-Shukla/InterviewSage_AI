import React from 'react';
import { History, FileCode, CheckCircle, Hash } from 'lucide-react';
import { PromptHistoryItem } from '../types/admin.types';

interface PromptHistoryExplorerProps {
  promptHistory?: PromptHistoryItem[];
}

export const PromptHistoryExplorer: React.FC<PromptHistoryExplorerProps> = ({ promptHistory }) => {
  if (!promptHistory || promptHistory.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Prompt Version History Explorer</h2>
        </div>
        <p className="text-xs text-slate-400">No prompt version history records available.</p>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <History className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">
            Prompt Version History Explorer
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">{promptHistory.length} Registered Templates</span>
      </div>

      <div className="space-y-3">
        {promptHistory.map((item) => (
          <div
            key={`${item.prompt_key}-${item.version}`}
            className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/60 space-y-2"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <FileCode className="w-4 h-4 text-indigo-400 shrink-0" />
                <span className="font-mono font-bold text-slate-100 text-xs">
                  {item.prompt_key}
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-indigo-950/80 border border-indigo-800/60 text-indigo-300">
                  v{item.version}
                </span>
              </div>

              {item.is_active && (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-400 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/30">
                  <CheckCircle className="w-3 h-3" /> Active
                </span>
              )}
            </div>

            {item.description && (
              <p className="text-xs text-slate-300 leading-relaxed font-mono pl-6">
                {item.description}
              </p>
            )}

            {item.variables && item.variables.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pl-6 pt-1">
                {item.variables.map((variable) => (
                  <span
                    key={variable}
                    className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono bg-slate-900 border border-slate-800 text-slate-400"
                  >
                    <Hash className="w-3 h-3 text-slate-500" />
                    {variable}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
