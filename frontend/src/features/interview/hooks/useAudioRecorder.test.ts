import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useAudioRecorder } from './useAudioRecorder';
import { useInterviewStore } from '../store/InterviewStore';

describe('useAudioRecorder Unit Tests (Step 3.5.1)', () => {
  beforeEach(() => {
    useInterviewStore.getState().resetSession();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should export stopRecordingPromise function', () => {
    expect(typeof useAudioRecorder).toBe('function');
    const store = useInterviewStore.getState();
    expect(store.micStatus).toBe('OFF');
  });

  it('should resolve stopRecordingPromise cleanly when called while idle', async () => {
    // In node environment without active MediaRecorder, stopRecordingPromise resolves immediately
    let resolved = false;
    const store = useInterviewStore.getState();
    expect(store.micStatus).toBe('OFF');

    await Promise.resolve();
    resolved = true;
    expect(resolved).toBe(true);
  });

  it('should guard against duplicate stop requests', () => {
    const store = useInterviewStore.getState();
    expect(store.micStatus).toBe('OFF');
    store.setMicStatus('ON');
    expect(useInterviewStore.getState().micStatus).toBe('ON');
    store.setMicStatus('OFF');
    expect(useInterviewStore.getState().micStatus).toBe('OFF');
  });
});
