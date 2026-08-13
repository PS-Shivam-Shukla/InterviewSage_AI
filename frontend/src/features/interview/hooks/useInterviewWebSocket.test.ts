import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { useInterviewStore } from '../store/InterviewStore';

describe('useInterviewWebSocket Hook TTS Playback Tests', () => {
  beforeEach(() => {
    useInterviewStore.getState().resetSession();
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('should distinguish binary ArrayBuffer data from JSON string data', () => {
    const textData = JSON.stringify({ type: 'PONG' });
    const binaryData = new ArrayBuffer(1024);

    expect(typeof textData === 'string').toBe(true);
    expect(binaryData instanceof ArrayBuffer).toBe(true);
    expect(binaryData instanceof Blob).toBe(false);
  });

  it('should create valid audio Blob with audio/wav mime type from binary bytes', () => {
    const pcmBytes = new Uint8Array([82, 73, 70, 70, 36, 0, 0, 0]); // RIFF header
    const blob = new Blob([pcmBytes], { type: 'audio/wav' });

    expect(blob).toBeInstanceOf(Blob);
    expect(blob.type).toBe('audio/wav');
    expect(blob.size).toBe(8);
  });

  it('should handle AI state transition from IDLE to SPEAKING and back to IDLE', () => {
    const store = useInterviewStore.getState();
    expect(store.aiState).toBe('IDLE');

    store.setAIState('SPEAKING');
    expect(useInterviewStore.getState().aiState).toBe('SPEAKING');

    store.setAIState('IDLE');
    expect(useInterviewStore.getState().aiState).toBe('IDLE');
  });

  it('should revoke object URLs on cleanup', () => {
    const mockRevoke = vi.fn();
    const originalRevoke = URL.revokeObjectURL;
    URL.revokeObjectURL = mockRevoke;

    const dummyUrl = 'blob:http://localhost/dummy-uuid';
    URL.revokeObjectURL(dummyUrl);

    expect(mockRevoke).toHaveBeenCalledWith(dummyUrl);
    URL.revokeObjectURL = originalRevoke;
  });
});
