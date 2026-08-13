import React from 'react';
import { cn } from '../lib/utils';

export interface ProgressProps {
  value: number; // 0 to 100
  max?: number;
  label?: string;
  showValue?: boolean;
  className?: string;
  barClassName?: string;
}

export const Progress: React.FC<ProgressProps> = ({
  value,
  max = 100,
  label,
  showValue = false,
  className,
  barClassName,
}) => {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn('w-full flex flex-col space-y-1.5', className)}>
      {(label || showValue) && (
        <div className="flex justify-between items-center text-xs font-medium text-slate-300">
          {label && <span>{label}</span>}
          {showValue && <span>{Math.round(percentage)}%</span>}
        </div>
      )}
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-800 border border-slate-700/50">
        <div
          className={cn('h-full bg-indigo-600 transition-all duration-300 ease-out rounded-full', barClassName)}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
