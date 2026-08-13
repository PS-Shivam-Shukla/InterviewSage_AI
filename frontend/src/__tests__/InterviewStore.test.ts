import { describe, it, expect, beforeEach } from 'vitest';
import { useInterviewStore } from '../features/interview/store/InterviewStore';

describe('InterviewStore Unit Tests', () => {
  beforeEach(() => {
    useInterviewStore.getState().resetSession();
  });

  it('should initialize with default state', () => {
    const state = useInterviewStore.getState();
    expect(state.aiState).toBe('IDLE');
    expect(state.isMuted).toBe(false);
    expect(state.isPaused).toBe(false);
    expect(state.wsConnected).toBe(false);
    expect(state.transcriptEntries).toEqual([]);
  });

  it('should update AI state correctly', () => {
    useInterviewStore.getState().setAIState('SPEAKING');
    expect(useInterviewStore.getState().aiState).toBe('SPEAKING');

    useInterviewStore.getState().setAIState('LISTENING');
    expect(useInterviewStore.getState().aiState).toBe('LISTENING');
  });

  it('should add transcript entries', () => {
    const entry = {
      id: 'entry-1',
      speaker: 'AI' as const,
      text: 'Hello, welcome to InterviewSage AI.',
      timestamp: new Date().toISOString(),
    };

    useInterviewStore.getState().addTranscriptEntry(entry);
    expect(useInterviewStore.getState().transcriptEntries).toHaveLength(1);
    expect(useInterviewStore.getState().transcriptEntries[0].text).toBe('Hello, welcome to InterviewSage AI.');
  });

  it('should update metrics', () => {
    useInterviewStore.getState().updateMetrics({ technicalScore: 98, wpm: 160 });
    expect(useInterviewStore.getState().metrics.technicalScore).toBe(98);
    expect(useInterviewStore.getState().metrics.wpm).toBe(160);
  });

  it('should reset session state', () => {
    useInterviewStore.getState().setAIState('SPEAKING');
    useInterviewStore.getState().setIsMuted(true);
    useInterviewStore.getState().resetSession();

    expect(useInterviewStore.getState().aiState).toBe('IDLE');
    expect(useInterviewStore.getState().isMuted).toBe(false);
  });
});
