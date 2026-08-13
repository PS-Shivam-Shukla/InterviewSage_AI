import React from 'react';
import { LoadingSpinner } from './LoadingSpinner';

export interface LoadingOverlayProps {
  isVisible: boolean;
  message?: string;
}

export const LoadingOverlay: React.FC<LoadingOverlayProps> = ({ isVisible, message = 'Loading...' }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="flex flex-col items-center space-y-3 p-6 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl">
        <LoadingSpinner size="lg" />
        <p className="text-sm font-medium text-slate-200">{message}</p>
      </div>
    </div>
  );
};
