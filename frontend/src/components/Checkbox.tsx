import React from 'react';
import { cn } from '../lib/utils';

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  description?: string;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, label, description, id, ...props }, ref) => {
    const checkboxId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

    return (
      <div className="flex items-start space-x-3">
        <input
          id={checkboxId}
          type="checkbox"
          ref={ref}
          className={cn(
            'h-4 w-4 rounded border-slate-700 bg-slate-900 text-indigo-600 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-slate-900 transition-colors',
            className
          )}
          {...props}
        />
        {(label || description) && (
          <div className="flex flex-col">
            {label && (
              <label htmlFor={checkboxId} className="text-sm font-medium text-slate-200 cursor-pointer">
                {label}
              </label>
            )}
            {description && <span className="text-xs text-slate-400">{description}</span>}
          </div>
        )}
      </div>
    );
  }
);

Checkbox.displayName = 'Checkbox';
