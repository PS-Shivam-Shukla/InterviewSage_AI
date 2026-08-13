import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Bell, Check, Trash2, FileText, Mic, Brain, Shield } from 'lucide-react';

export interface NotificationItem {
  id: string;
  category: 'interview' | 'resume' | 'career' | 'system';
  title: string;
  message: string;
  timestamp: string;
  read: boolean;
}

export const NotificationBell: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<NotificationItem[]>([
    {
      id: 'notif-1',
      category: 'resume',
      title: 'Resume Parsing Completed',
      message: 'Alex_Resume_2026.pdf parsed with 98% ATS Score.',
      timestamp: '5m ago',
      read: false,
    },
    {
      id: 'notif-2',
      category: 'interview',
      title: 'Voice Interview Finalized',
      message: 'Senior AI Architect evaluation rating: Strong Hire.',
      timestamp: '1h ago',
      read: false,
    },
    {
      id: 'notif-3',
      category: 'career',
      title: 'Memory Roadmap Synchronized',
      message: 'Updated target focus on PostgreSQL checkpointers.',
      timestamp: '3h ago',
      read: true,
    },
  ]);

  const unreadCount = notifications.filter((n) => !n.read).length;

  const markAllRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'resume':
        return <FileText className="w-4 h-4 text-indigo-400" />;
      case 'interview':
        return <Mic className="w-4 h-4 text-emerald-400" />;
      case 'career':
        return <Brain className="w-4 h-4 text-amber-400" />;
      case 'system':
      default:
        return <Shield className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 rounded-xl text-slate-400 hover:text-slate-100 hover:bg-slate-800/60 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
        aria-label="Open Notifications"
        aria-expanded={isOpen}
      >
        <Bell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute top-1.5 right-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white shadow-md animate-pulse">
            {unreadCount}
          </span>
        )}
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              className="absolute right-0 mt-2 z-50 w-80 sm:w-96 rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl overflow-hidden"
            >
              <div className="flex items-center justify-between p-3.5 border-b border-slate-800 bg-slate-950">
                <div className="flex items-center space-x-2">
                  <Bell className="w-4 h-4 text-indigo-400" />
                  <span className="text-xs font-bold text-slate-100">Notifications</span>
                  {unreadCount > 0 && (
                    <span className="rounded-full bg-rose-950 px-2 py-0.5 text-[10px] font-bold text-rose-300 border border-rose-800/50">
                      {unreadCount} new
                    </span>
                  )}
                </div>

                <div className="flex items-center space-x-1">
                  <button
                    onClick={markAllRead}
                    className="p-1 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800"
                    title="Mark all read"
                  >
                    <Check className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={clearAll}
                    className="p-1 rounded text-slate-400 hover:text-rose-400 hover:bg-slate-800"
                    title="Clear all"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="max-h-72 overflow-y-auto p-2 space-y-2">
                {notifications.length > 0 ? (
                  notifications.map((item) => (
                    <div
                      key={item.id}
                      className={`p-3 rounded-xl border transition-all text-xs space-y-1 ${
                        item.read
                          ? 'bg-slate-950/40 border-slate-800/60 opacity-70'
                          : 'bg-slate-950 border-indigo-500/40'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <div className="flex items-center space-x-2">
                          {getCategoryIcon(item.category)}
                          <span className="font-bold text-slate-100">{item.title}</span>
                        </div>
                        <span className="text-[10px] text-slate-500 font-mono">{item.timestamp}</span>
                      </div>
                      <p className="text-slate-300 leading-relaxed pl-6">{item.message}</p>
                    </div>
                  ))
                ) : (
                  <div className="p-6 text-center text-xs text-slate-500">No notifications.</div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};
