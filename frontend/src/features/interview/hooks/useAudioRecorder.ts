import { useState, useRef, useCallback, useEffect } from 'react';
import { useInterviewStore, MicStatus } from '../store/InterviewStore';

export type RecorderState = 'IDLE' | 'REQUESTING_PERMISSION' | 'READY' | 'RECORDING' | 'ERROR';

export interface UseAudioRecorderOptions {
  timeslice?: number;
  onAudioChunk?: (chunk: Blob) => void;
  onStateChange?: (state: RecorderState) => void;
  onError?: (error: Error) => void;
}

export interface UseAudioRecorderReturn {
  isRecording: boolean;
  isStopping: boolean;
  recorderState: RecorderState;
  micStatus: MicStatus;
  micLevel: number;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  stopRecordingPromise: () => Promise<void>;
}

function getSupportedMimeType(): string {
  const mimeTypes = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/ogg;codecs=opus',
    'audio/mp4',
    'audio/wav',
  ];
  for (const mime of mimeTypes) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(mime)) {
      return mime;
    }
  }
  return '';
}

export function useAudioRecorder(options: UseAudioRecorderOptions = {}): UseAudioRecorderReturn {
  const { timeslice = 250, onAudioChunk, onStateChange, onError } = options;

  const [isRecording, setIsRecording] = useState<boolean>(false);
  const [isStopping, setIsStopping] = useState<boolean>(false);
  const [recorderState, setRecorderStateInternal] = useState<RecorderState>('IDLE');
  const [micLevelState, setMicLevelState] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  const { setMicStatus, setMicLevel } = useInterviewStore();

  const mediaStreamRef = useRef<MediaStream | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const sourceNodeRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const dataArrayRef = useRef<Uint8Array | null>(null);
  const isRecordingRef = useRef<boolean>(false);
  const isStoppingRef = useRef<boolean>(false);
  const stopPromiseRef = useRef<Promise<void> | null>(null);

  const updateState = useCallback(
    (newState: RecorderState) => {
      setRecorderStateInternal(newState);
      if (onStateChange) onStateChange(newState);

      // Sync with Zustand InterviewStore
      switch (newState) {
        case 'REQUESTING_PERMISSION':
          setMicStatus('REQUESTING');
          break;
        case 'RECORDING':
        case 'READY':
          setMicStatus('ON');
          break;
        case 'ERROR':
          setMicStatus('ERROR');
          break;
        case 'IDLE':
        default:
          setMicStatus('OFF');
          break;
      }
    },
    [onStateChange, setMicStatus]
  );

  const cleanup = useCallback(() => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // Ignore inactive state stop errors
      }
    }
    mediaRecorderRef.current = null;

    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }

    if (sourceNodeRef.current) {
      sourceNodeRef.current.disconnect();
      sourceNodeRef.current = null;
    }

    if (analyserRef.current) {
      analyserRef.current.disconnect();
      analyserRef.current = null;
    }

    if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
      try {
        audioContextRef.current.close();
      } catch {
        // Ignore close errors
      }
      audioContextRef.current = null;
    }

    isRecordingRef.current = false;
    isStoppingRef.current = false;
    setIsRecording(false);
    setIsStopping(false);
    setMicLevelState(0);
    setMicLevel(0);
  }, [setMicLevel]);

  const updateVolume = useCallback(() => {
    if (!analyserRef.current || !dataArrayRef.current) return;

    analyserRef.current.getByteFrequencyData(dataArrayRef.current as any);
    let sum = 0;
    for (let i = 0; i < dataArrayRef.current.length; i++) {
      sum += dataArrayRef.current[i];
    }
    const average = sum / dataArrayRef.current.length;
    // Normalize byte frequency average to 0-100 micLevel scale
    const normalized = Math.min(100, Math.round((average / 128) * 100));

    setMicLevelState(normalized);
    setMicLevel(normalized);

    if (isRecordingRef.current && !isStoppingRef.current) {
      animFrameRef.current = requestAnimationFrame(updateVolume);
    }
  }, [setMicLevel]);

  const startRecording = useCallback(async () => {
    if (isRecordingRef.current || isStoppingRef.current) return;

    setError(null);
    updateState('REQUESTING_PERMISSION');

    if (typeof window === 'undefined' || !navigator?.mediaDevices?.getUserMedia) {
      const errMsg = 'Microphone access is not supported in your current browser or connection environment.';
      const err = new Error(errMsg);
      setError(errMsg);
      updateState('ERROR');
      if (onError) onError(err);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 16000,
        },
      });

      mediaStreamRef.current = stream;

      // Initialize Web Audio API AnalyserNode
      const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
      if (AudioCtx) {
        const audioCtx = new AudioCtx();
        audioContextRef.current = audioCtx;

        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        analyserRef.current = analyser;

        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);
        sourceNodeRef.current = source;

        dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);
      }

      // Initialize MediaRecorder
      const mimeType = getSupportedMimeType();
      const recorderOptions = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(stream, recorderOptions);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0 && onAudioChunk) {
          onAudioChunk(event.data);
        }
      };

      mediaRecorder.onerror = (event: any) => {
        const recorderErr = new Error(`MediaRecorder error: ${event.error?.name || 'Unknown'}`);
        setError(recorderErr.message);
        updateState('ERROR');
        if (onError) onError(recorderErr);
      };

      mediaRecorder.onstop = () => {
        updateState('READY');
      };

      mediaRecorder.start(timeslice);
      isRecordingRef.current = true;
      setIsRecording(true);
      updateState('RECORDING');

      // Start volume animation loop
      if (analyserRef.current) {
        updateVolume();
      }
    } catch (err: any) {
      cleanup();
      let userMsg = 'Failed to access microphone.';
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        userMsg = 'Microphone permission was denied. Please allow microphone access in browser settings.';
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        userMsg = 'No microphone device found on your system.';
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        userMsg = 'Microphone is currently in use by another application.';
      } else if (err.message) {
        userMsg = err.message;
      }

      setError(userMsg);
      updateState('ERROR');
      if (onError) onError(err instanceof Error ? err : new Error(userMsg));
    }
  }, [timeslice, onAudioChunk, onError, updateState, updateVolume, cleanup]);

  const stopRecordingPromise = useCallback(async (): Promise<void> => {
    if (stopPromiseRef.current) {
      return stopPromiseRef.current;
    }

    if (!isRecordingRef.current && !mediaRecorderRef.current) {
      return Promise.resolve();
    }

    isStoppingRef.current = true;
    setIsStopping(true);

    const promise = new Promise<void>((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder || recorder.state === 'inactive') {
        cleanup();
        updateState('READY');
        resolve();
        return;
      }

      const originalOnStop = recorder.onstop;
      recorder.onstop = (event: Event) => {
        if (originalOnStop) {
          try {
            originalOnStop.call(recorder, event);
          } catch {
            // Ignore callback error
          }
        }
        cleanup();
        updateState('READY');
        resolve();
      };

      try {
        recorder.stop();
      } catch {
        cleanup();
        updateState('READY');
        resolve();
      }
    });

    stopPromiseRef.current = promise;
    return promise.finally(() => {
      stopPromiseRef.current = null;
    });
  }, [cleanup, updateState]);

  const stopRecording = useCallback(() => {
    stopRecordingPromise();
  }, [stopRecordingPromise]);

  // Clean up on component unmount
  useEffect(() => {
    return () => {
      cleanup();
    };
  }, [cleanup]);

  const storeMicStatus = useInterviewStore((state) => state.micStatus);

  return {
    isRecording,
    isStopping,
    recorderState,
    micStatus: storeMicStatus,
    micLevel: micLevelState,
    error,
    startRecording,
    stopRecording,
    stopRecordingPromise,
  };
}
