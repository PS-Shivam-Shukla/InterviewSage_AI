import React from 'react';
import { Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  label?: string;
}

const sizeMap = {
  sm: 'w-4 h-4',
  md: 'w-6 h-6',
  lg: 'w-8 h-8',
  xl: 'w-12 h-12',
};

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ size = 'md', className, label }) => {
  return (
    <div className="flex flex-col items-center justify-center space-y-2">
      <Loader2 className={cn('animate-spin text-indigo-500', sizeMap[size], className)} />
      {label && <span className="text-xs text-slate-400 font-medium">{label}</span>}
    </div>
  );
};
