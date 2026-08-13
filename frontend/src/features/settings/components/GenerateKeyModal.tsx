import { useState } from 'react';
import { X, Key, Copy, CheckCircle2 } from 'lucide-react';
import { Button } from '../../../components/ui/Button';

interface GenerateKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onGenerate: (name: string) => Promise<string | null>;
}

export function GenerateKeyModal({ isOpen, onClose, onGenerate }: GenerateKeyModalProps) {
  const [keyName, setKeyName] = useState('');
  const [generatedKey, setGeneratedKey] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!isOpen) return null;

  const handleGenerateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!keyName.trim()) return;

    setIsGenerating(true);
    const key = await onGenerate(keyName);
    setIsGenerating(false);
    if (key) {
      setGeneratedKey(key);
    }
  };

  const handleCopy = () => {
    if (generatedKey) {
      navigator.clipboard.writeText(generatedKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleCloseModal = () => {
    setKeyName('');
    setGeneratedKey(null);
    setCopied(false);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-xs animate-in fade-in">
      <div className="w-full max-w-md rounded-2xl border border-neutral-200 bg-white p-6 shadow-2xl dark:border-neutral-800 dark:bg-neutral-900 space-y-6">
        <div className="flex items-center justify-between pb-2 border-b border-neutral-200 dark:border-neutral-800">
          <div className="flex items-center gap-2">
            <div className="rounded-xl bg-blue-600/10 p-2 text-blue-600 dark:bg-blue-500/15 dark:text-blue-400">
              <Key className="h-5 w-5" />
            </div>
            <h3 className="text-base font-bold text-neutral-900 dark:text-white font-display">
              Generate New API Key
            </h3>
          </div>

          <button
            type="button"
            onClick={handleCloseModal}
            className="rounded-lg p-1.5 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-700 dark:hover:bg-neutral-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {!generatedKey ? (
          <form onSubmit={handleGenerateSubmit} className="space-y-4">
            <div className="space-y-1">
              <label className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                Key Label / Description
              </label>
              <input
                type="text"
                value={keyName}
                onChange={(e) => setKeyName(e.target.value)}
                placeholder="e.g. Staging CI/CD Integration Key"
                required
                className="w-full rounded-xl border border-neutral-200/90 bg-neutral-50/50 px-3.5 py-2 text-xs text-neutral-900 focus:bg-white focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-neutral-800 dark:bg-neutral-950/50 dark:text-white transition-all"
              />
            </div>

            <div className="pt-2 flex justify-end gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={handleCloseModal}
                className="rounded-xl text-xs"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                size="sm"
                disabled={!keyName.trim() || isGenerating}
                className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4"
              >
                {isGenerating ? 'Generating Key...' : 'Generate Secret Key'}
              </Button>
            </div>
          </form>
        ) : (
          <div className="space-y-4">
            <div className="p-3.5 rounded-xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200 dark:border-amber-900/30 text-xs text-amber-800 dark:text-amber-300">
              <p className="font-bold">One-Time Secret Key Reveal</p>
              <p className="mt-0.5 text-[11px]">
                Please copy and store this API key securely. It will not be shown again!
              </p>
            </div>

            <div className="space-y-1">
              <label className="text-xs font-bold text-neutral-800 dark:text-neutral-200">
                Your Secret API Key
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  readOnly
                  value={generatedKey}
                  className="w-full rounded-xl border border-neutral-200 bg-neutral-100 font-mono text-xs text-neutral-900 p-2.5 dark:border-neutral-800 dark:bg-neutral-950 dark:text-emerald-400"
                />
                <Button
                  type="button"
                  size="sm"
                  onClick={handleCopy}
                  className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs px-3.5 shrink-0"
                >
                  {copied ? (
                    <>
                      <CheckCircle2 className="mr-1 h-3.5 w-3.5" /> Copied
                    </>
                  ) : (
                    <>
                      <Copy className="mr-1 h-3.5 w-3.5" /> Copy
                    </>
                  )}
                </Button>
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <Button type="button" size="sm" onClick={handleCloseModal} className="rounded-xl text-xs">
                Done & Close
              </Button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
