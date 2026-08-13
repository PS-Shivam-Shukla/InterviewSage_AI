import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Loader2,
  MessageSquare,
  AlertCircle,
  Mic,
  Square,
  Edit3,
  Volume2,
  WifiOff,
} from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { LiveRegion } from '../../../components/ui/LiveRegion';
import { cn } from '../../../lib/utils';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { useInterviewWebSocket } from '../hooks/useInterviewWebSocket';
import { useInterviewStore } from '../store/InterviewStore';
import { WaveformVisualizer } from './WaveformVisualizer';

export interface InterviewAnswerInputProps {
  onSubmit: (answerText: string) => void;
  isSubmitting: boolean;
  isDisabled?: boolean;
  error?: string | null;
  className?: string;
  interviewId?: string;
  onVoiceTurnComplete?: (data: any) => void;
}

export const InterviewAnswerInput: React.FC<InterviewAnswerInputProps> = ({
  onSubmit,
  isSubmitting,
  isDisabled = false,
  error,
  className,
  interviewId,
  onVoiceTurnComplete,
}) => {
  const [inputMode, setInputMode] = useState<'TEXT' | 'VOICE'>('TEXT');
  const [answer, setAnswer] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const { aiState, wsConnected, setAIState } = useInterviewStore();

  const handleVoiceTurnDone = (data: any) => {
    if (data?.candidate_transcript) {
      setAnswer(data.candidate_transcript);
    }
    if (onVoiceTurnComplete) {
      onVoiceTurnComplete(data);
    }
  };

  const { sendAudioChunk, endCandidateSpeech } = useInterviewWebSocket(interviewId, handleVoiceTurnDone);

  const {
    isRecording,
    isStopping,
    micStatus,
    micLevel,
    error: micError,
    startRecording,
    stopRecordingPromise,
  } = useAudioRecorder({
    onAudioChunk: (chunk) => {
      sendAudioChunk(chunk);
    },
  });

  // Handle Text Mode Submission
  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim()) {
      setValidationError('Please enter a response before submitting.');
      return;
    }
    setValidationError(null);
    onSubmit(answer.trim());
    setAnswer('');
  };

  // Handle Keyboard Ctrl+Enter Submission
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleTextSubmit(e);
    }
  };

  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        let currentTranscript = '';
        for (let i = 0; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        if (currentTranscript.trim()) {
          setAnswer(currentTranscript);
        }
      };

      recognition.onerror = (event: any) => {
        console.warn('SpeechRecognition error:', event.error);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  // Handle Voice Turn Start
  const handleStartVoiceTurn = async () => {
    setValidationError(null);
    setAIState('LISTENING');
    if (recognitionRef.current) {
      try {
        recognitionRef.current.start();
      } catch {
        // Ignore if already listening
      }
    }
    try {
      await startRecording();
    } catch (err) {
      console.error('Failed to start voice recording:', err);
      setAIState('IDLE');
    }
  };

  // Handle Voice Turn End
  const handleStopVoiceTurn = async () => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {
        // Ignore if already stopped
      }
    }
    try {
      await stopRecordingPromise();
      endCandidateSpeech();
      setAIState('THINKING');
    } catch (err) {
      console.error('Error stopping audio recorder:', err);
      setAIState('IDLE');
    }
  };

  const isControlsDisabled = isDisabled || isSubmitting || isStopping;

  // Compute live announcement message for screen readers
  const getLiveAnnouncement = () => {
    if (isRecording) return 'Microphone recording active. Speak your response.';
    if (aiState === 'THINKING' || isSubmitting) return 'Evaluating candidate response.';
    if (aiState === 'SPEAKING') return 'AI interviewer speaking response.';
    return null;
  };

  return (
    <div className={cn('rounded-2xl border border-slate-800 bg-slate-900/90 p-5 shadow-xl space-y-4', className)}>
      <LiveRegion message={getLiveAnnouncement()} />

      {/* Mode Switcher Tabs */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <MessageSquare className="w-4 h-4 text-indigo-400" aria-hidden="true" />
          <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider">Candidate Response</h3>
        </div>

        <div className="flex items-center p-1 rounded-xl bg-slate-950 border border-slate-800" role="tablist" aria-label="Input Mode Switcher">
          <button
            type="button"
            role="tab"
            aria-selected={inputMode === 'TEXT'}
            onClick={() => setInputMode('TEXT')}
            className={cn(
              'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500',
              inputMode === 'TEXT'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            )}
          >
            <Edit3 className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Text Mode</span>
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={inputMode === 'VOICE'}
            onClick={() => setInputMode('VOICE')}
            className={cn(
              'flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500',
              inputMode === 'VOICE'
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
            )}
          >
            <Mic className="w-3.5 h-3.5" aria-hidden="true" />
            <span>Voice Streaming</span>
          </button>
        </div>
      </div>

      {/* Error Alert Display */}
      {(error || validationError || micError) && (
        <div className="flex items-center space-x-2 p-3 rounded-xl bg-rose-950/40 border border-rose-900/60 text-xs text-rose-300">
          <AlertCircle className="w-4 h-4 shrink-0" aria-hidden="true" />
          <span>{error || validationError || micError}</span>
        </div>
      )}

      {/* Mode 1: Text Mode Input Form */}
      {inputMode === 'TEXT' && (
        <form onSubmit={handleTextSubmit} className="space-y-3">
          <div className="flex justify-between items-center text-[11px] text-slate-400 font-mono">
            <span>Type your response (Ctrl + Enter to submit)</span>
            <span>{answer.length} chars</span>
          </div>

          <textarea
            value={answer}
            onChange={(e) => {
              setAnswer(e.target.value);
              if (validationError) setValidationError(null);
            }}
            onKeyDown={handleKeyDown}
            placeholder="Explain system design choices, algorithms, and trade-offs clearly..."
            disabled={isControlsDisabled}
            rows={4}
            aria-label="Text answer input field"
            aria-invalid={!!validationError}
            className={cn(
              'w-full p-4 rounded-xl bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500 transition-all resize-none text-sm leading-relaxed',
              isControlsDisabled && 'opacity-60 cursor-not-allowed bg-slate-900'
            )}
          />

          <div className="flex justify-end">
            <Button
              type="submit"
              disabled={isControlsDisabled || !answer.trim()}
              className="bg-indigo-600 hover:bg-indigo-500 text-white font-semibold shadow-lg shadow-indigo-600/30 px-6 py-2.5 rounded-xl transition-all flex items-center space-x-2"
            >
              {isSubmitting || aiState === 'THINKING' ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  <span>Evaluating Answer...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" aria-hidden="true" />
                  <span>Submit Text Answer</span>
                </>
              )}
            </Button>
          </div>
        </form>
      )}

      {/* Mode 2: Voice Mode Interface */}
      {inputMode === 'VOICE' && (
        <div className="py-6 px-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex flex-col items-center justify-center space-y-6 text-center">
          {/* WebSocket Availability Check */}
          {!wsConnected && (
            <div className="flex items-center space-x-2 text-amber-400 bg-amber-950/40 border border-amber-900/50 px-4 py-2 rounded-xl text-xs">
              <WifiOff className="w-4 h-4" aria-hidden="true" />
              <span>Voice WebSocket connection offline. Waiting to connect...</span>
            </div>
          )}

          {/* Real Audio Waveform Visualizer */}
          <div className="py-2">
            <WaveformVisualizer micLevel={micLevel} isActive={isRecording} width={260} height={44} />
          </div>

          {/* Dynamic Record Button Control */}
          <div className="space-y-3">
            {isRecording ? (
              <Button
                type="button"
                onClick={handleStopVoiceTurn}
                aria-label="Stop microphone recording and submit speech"
                className="bg-rose-600 hover:bg-rose-500 text-white font-bold px-8 py-3.5 rounded-2xl shadow-xl shadow-rose-600/40 transition-all flex items-center space-x-3 text-sm animate-pulse"
              >
                <Square className="w-5 h-5 fill-current" aria-hidden="true" />
                <span>Stop Recording & Submit Speech</span>
              </Button>
            ) : aiState === 'THINKING' || isSubmitting ? (
              <Button
                type="button"
                disabled
                aria-label="Evaluating candidate speech"
                className="bg-amber-600/80 text-white font-semibold px-8 py-3.5 rounded-2xl cursor-not-allowed flex items-center space-x-3 text-sm opacity-90"
              >
                <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
                <span>Evaluating Candidate Speech...</span>
              </Button>
            ) : aiState === 'SPEAKING' ? (
              <Button
                type="button"
                disabled
                aria-label="AI interviewer speaking"
                className="bg-indigo-600/80 text-white font-semibold px-8 py-3.5 rounded-2xl cursor-not-allowed flex items-center space-x-3 text-sm opacity-90"
              >
                <Volume2 className="w-5 h-5 animate-pulse" aria-hidden="true" />
                <span>AI Interviewer Speaking...</span>
              </Button>
            ) : (
              <Button
                type="button"
                onClick={handleStartVoiceTurn}
                disabled={isControlsDisabled || !wsConnected}
                aria-label="Start recording speech answer"
                className="bg-indigo-600 hover:bg-indigo-500 text-white font-bold px-8 py-3.5 rounded-2xl shadow-xl shadow-indigo-600/40 transition-all flex items-center space-x-3 text-sm"
              >
                <Mic className="w-5 h-5" aria-hidden="true" />
                <span>Start Recording Speech Answer</span>
              </Button>
            )}

            <div className="text-xs font-mono text-slate-400">
              {micStatus === 'REQUESTING' && 'Requesting microphone permission...'}
              {micStatus === 'ON' && 'Microphone active — speak your response clearly'}
              {micStatus === 'OFF' && 'Click microphone button to begin voice response'}
              {micStatus === 'ERROR' && 'Microphone error — verify permission settings'}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
