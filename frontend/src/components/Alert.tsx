import React from 'react';
import { AlertCircle, CheckCircle2, Info, AlertTriangle } from 'lucide-react';
import { cn } from '../lib/utils';

export interface AlertProps {
  variant?: 'info' | 'success' | 'warning' | 'destructive';
  title?: string;
  children: React.ReactNode;
  className?: string;
}

const variantStyles = {
  info: 'bg-indigo-950/40 border-indigo-800/60 text-indigo-200',
  success: 'bg-emerald-950/40 border-emerald-800/60 text-emerald-200',
  warning: 'bg-amber-950/40 border-amber-800/60 text-amber-200',
  destructive: 'bg-rose-950/40 border-rose-800/60 text-rose-200',
};

const variantIcons = {
  info: <Info className="w-5 h-5 text-indigo-400" />,
  success: <CheckCircle2 className="w-5 h-5 text-emerald-400" />,
  warning: <AlertTriangle className="w-5 h-5 text-amber-400" />,
  destructive: <AlertCircle className="w-5 h-5 text-rose-400" />,
};

export const Alert: React.FC<AlertProps> = ({ variant = 'info', title, children, className }) => {
  return (
    <div className={cn('flex items-start space-x-3 p-4 rounded-xl border text-sm', variantStyles[variant], className)}>
      <div className="flex-shrink-0 mt-0.5">{variantIcons[variant]}</div>
      <div className="flex-1">
        {title && <h4 className="font-semibold mb-1 text-slate-100">{title}</h4>}
        <div className="text-xs leading-relaxed">{children}</div>
      </div>
    </div>
  );
};
