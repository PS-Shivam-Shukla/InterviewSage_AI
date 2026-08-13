import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ShieldCheck } from 'lucide-react';
import { cn } from '../../../lib/utils';

export interface DragDropUploaderProps {
  onFileSelected: (file: File) => void;
  allowedExtensions?: string[];
  maxSizeBytes?: number;
  disabled?: boolean;
}

export const DragDropUploader: React.FC<DragDropUploaderProps> = ({
  onFileSelected,
  allowedExtensions = ['.pdf', '.docx', '.txt'],
  maxSizeBytes = 10 * 1024 * 1024,
  disabled = false,
}) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): boolean => {
    setError(null);
    const ext = '.' + file.name.split('.').pop()?.toLowerCase();

    if (!allowedExtensions.includes(ext)) {
      setError(`Invalid format "${ext}". Allowed: ${allowedExtensions.join(', ')}`);
      return false;
    }

    if (file.size > maxSizeBytes) {
      setError(`File size exceeds ${(maxSizeBytes / (1024 * 1024)).toFixed(0)}MB limit.`);
      return false;
    }

    return true;
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        onFileSelected(file);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        onFileSelected(file);
      }
    }
  };

  return (
    <div className="w-full flex flex-col space-y-3">
      <motion.div
        whileHover={{ scale: disabled ? 1 : 1.005 }}
        whileTap={{ scale: disabled ? 1 : 0.995 }}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
        className={cn(
          'relative flex flex-col items-center justify-center p-10 rounded-2xl border-2 border-dashed transition-all duration-300 cursor-pointer select-none text-center bg-gradient-to-b from-slate-900/90 to-slate-950',
          isDragOver
            ? 'border-indigo-500 bg-indigo-950/30 ring-4 ring-indigo-500/20 shadow-2xl scale-[1.01]'
            : 'border-slate-800 hover:border-indigo-500/50 hover:bg-slate-900 shadow-lg',
          disabled && 'cursor-not-allowed opacity-60'
        )}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={allowedExtensions.join(',')}
          onChange={handleFileChange}
          className="hidden"
          disabled={disabled}
        />

        {/* Animated Glow Halo */}
        <div
          className={cn(
            'flex h-16 w-16 items-center justify-center rounded-2xl transition-all duration-300 mb-4 shadow-xl border',
            isDragOver
              ? 'bg-indigo-600 text-white border-indigo-400 scale-110 shadow-indigo-500/50'
              : 'bg-indigo-950/60 text-indigo-400 border-indigo-800/50'
          )}
        >
          <UploadCloud className="w-8 h-8 animate-bounce" />
        </div>

        <h3 className="text-lg font-bold text-slate-100 tracking-tight">
          Drop your candidate resume here, or <span className="text-indigo-400 underline decoration-indigo-400/50">browse files</span>
        </h3>
        <p className="text-xs text-slate-400 mt-1 max-w-md leading-relaxed">
          Supports PDF, DOCX, or TXT (up to 10MB). Backend AI multi-agent engine will instantly extract skills, work history, and calculate ATS compatibility.
        </p>

        <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
          <div className="flex items-center space-x-1.5 rounded-full bg-slate-800/80 px-3 py-1 text-[11px] font-medium text-slate-300 border border-slate-700/60">
            <FileText className="w-3.5 h-3.5 text-indigo-400" />
            <span>PDF, DOCX, TXT</span>
          </div>
          <div className="flex items-center space-x-1.5 rounded-full bg-slate-800/80 px-3 py-1 text-[11px] font-medium text-slate-300 border border-slate-700/60">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Max 10MB</span>
          </div>
          <div className="flex items-center space-x-1.5 rounded-full bg-slate-800/80 px-3 py-1 text-[11px] font-medium text-slate-300 border border-slate-700/60">
            <ShieldCheck className="w-3.5 h-3.5 text-indigo-400" />
            <span>Secure Encryption</span>
          </div>
        </div>
      </motion.div>

      {error && (
        <motion.div
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center space-x-2 text-xs text-rose-400 bg-rose-950/40 p-3 rounded-xl border border-rose-800/50 shadow-sm"
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span className="font-medium">{error}</span>
        </motion.div>
      )}
    </div>
  );
};
