import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, CheckCircle2, Info, X, AlertTriangle } from 'lucide-react';
import { useNotificationStore } from '../stores/NotificationStore';

export const ToastProvider: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const { notifications, removeNotification } = useNotificationStore();

  const getIcon = (type: string) => {
    switch (type) {
      case 'success':
        return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-rose-400" />;
      case 'warning':
        return <AlertTriangle className="w-5 h-5 text-amber-400" />;
      default:
        return <Info className="w-5 h-5 text-indigo-400" />;
    }
  };

  return (
    <>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col space-y-2 max-w-md w-full px-4 pointer-events-none">
        <AnimatePresence>
          {notifications.map((toast) => (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="pointer-events-auto flex items-start space-x-3 p-4 bg-slate-900 border border-slate-700 text-slate-100 rounded-lg shadow-xl"
            >
              {getIcon(toast.type)}
              <div className="flex-1 text-sm">
                <h4 className="font-semibold text-slate-100">{toast.title}</h4>
                {toast.message && <p className="text-slate-300 mt-1">{toast.message}</p>}
              </div>
              <button
                onClick={() => removeNotification(toast.id)}
                className="text-slate-400 hover:text-slate-200 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </>
  );
};
