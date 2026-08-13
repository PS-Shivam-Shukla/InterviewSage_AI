import { useEffect, useRef, useCallback } from 'react';
import { ENV } from '../../../config/env.config';
import { useAuthStore } from '../../../stores/AuthStore';
import { useInterviewStore } from '../store/InterviewStore';

export function useInterviewWebSocket(
  interviewId?: string,
  onTurnComplete?: (data: any) => void
) {
  const wsRef = useRef<WebSocket | null>(null);
  const pingStartTimeRef = useRef<number>(0);
  const reconnectAttemptsRef = useRef<number>(0);

  const audioQueueRef = useRef<(ArrayBuffer | Blob)[]>([]);
  const isPlayingRef = useRef<boolean>(false);
  const activeAudioRef = useRef<HTMLAudioElement | null>(null);
  const currentObjectUrlRef = useRef<string | null>(null);

  const {
    setWsConnected,
    setLatencyMs,
    setAIState,
    addTranscriptEntry,
    updateMetrics,
  } = useInterviewStore();

  const cleanupCurrentAudio = useCallback(() => {
    if (activeAudioRef.current) {
      activeAudioRef.current.pause();
      activeAudioRef.current.onended = null;
      activeAudioRef.current.onerror = null;
      activeAudioRef.current = null;
    }
    if (currentObjectUrlRef.current) {
      try {
        URL.revokeObjectURL(currentObjectUrlRef.current);
      } catch {
        // Ignore revocation errors
      }
      currentObjectUrlRef.current = null;
    }
  }, []);

  const processAudioQueue = useCallback(async () => {
    if (isPlayingRef.current || audioQueueRef.current.length === 0) return;

    const audioData = audioQueueRef.current.shift();
    if (!audioData) return;

    isPlayingRef.current = true;
    setAIState('SPEAKING');

    try {
      const blob =
        audioData instanceof Blob
          ? audioData
          : new Blob([audioData], { type: 'audio/wav' });

      const objectUrl = URL.createObjectURL(blob);
      currentObjectUrlRef.current = objectUrl;

      const audio = new Audio();
      activeAudioRef.current = audio;
      audio.src = objectUrl;

      await new Promise<void>((resolve) => {
        const handleEnded = () => {
          cleanupCurrentAudio();
          resolve();
        };

        const handleError = () => {
          console.warn('TTS Audio Playback error or autoplay restriction');
          cleanupCurrentAudio();
          resolve();
        };

        audio.onended = handleEnded;
        audio.onerror = handleError as OnErrorEventHandler;

        audio.play().catch((err) => {
          console.warn('Browser autoplay prevented audio play:', err);
          cleanupCurrentAudio();
          resolve();
        });
      });
    } catch (err) {
      console.warn('Error creating or playing TTS audio blob:', err);
      cleanupCurrentAudio();
    } finally {
      isPlayingRef.current = false;
      setAIState('IDLE');
      if (audioQueueRef.current.length > 0) {
        processAudioQueue();
      }
    }
  }, [setAIState, cleanupCurrentAudio]);

  const enqueueAudioResponse = useCallback(
    (audioData: ArrayBuffer | Blob) => {
      audioQueueRef.current.push(audioData);
      processAudioQueue();
    },
    [processAudioQueue]
  );

  useEffect(() => {
    if (!interviewId) return;

    const token = useAuthStore.getState().tokens?.access_token?.replace(/^"|"$/g, '') || '';
    const wsUrl = `${ENV.WS_BASE_URL}/ws/interviews/${interviewId}?token=${encodeURIComponent(token)}`;

    let pingInterval: any;

    const connectWS = () => {
      try {
        const ws = new WebSocket(wsUrl);
        ws.binaryType = 'arraybuffer';
        wsRef.current = ws;

        ws.onopen = () => {
          setWsConnected(true);
          reconnectAttemptsRef.current = 0;

          pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
              pingStartTimeRef.current = Date.now();
              ws.send(JSON.stringify({ type: 'PING' }));
            }
          }, 5000);
        };

        ws.onmessage = (event) => {
          // 1. Binary Frame: TTS Audio Response
          if (event.data instanceof ArrayBuffer || event.data instanceof Blob) {
            enqueueAudioResponse(event.data);
            return;
          }

          // 2. Text Frame: Control Messages & Events
          try {
            const data = JSON.parse(event.data);

            if (data.type === 'PONG') {
              const rtt = Date.now() - pingStartTimeRef.current;
              setLatencyMs(rtt);
            } else if (data.type === 'AI_STATE_CHANGE') {
              setAIState(data.state);
            } else if (data.type === 'AI_SPEECH_CHUNK' || data.type === 'TRANSCRIPT_ENTRY') {
              addTranscriptEntry({
                id: data.id || Math.random().toString(36).substring(2, 9),
                speaker: data.speaker || 'AI',
                text: data.text || '',
                timestamp: data.timestamp || new Date().toISOString(),
              });
            } else if (data.type === 'METRICS_UPDATE') {
              updateMetrics(data.metrics);
            } else if (data.type === 'TURN_COMPLETE' || data.event === 'TURN_COMPLETE') {
              if (data.candidate_transcript) {
                addTranscriptEntry({
                  id: Math.random().toString(36).substring(2, 9),
                  speaker: 'CANDIDATE',
                  text: data.candidate_transcript,
                  timestamp: new Date().toISOString(),
                });
              }
              if (data.next_question?.question_text || data.agent_response) {
                addTranscriptEntry({
                  id: Math.random().toString(36).substring(2, 9),
                  speaker: 'AI',
                  text: data.next_question?.question_text || data.agent_response || '',
                  timestamp: new Date().toISOString(),
                });
              }
              if (data.live_scores) {
                updateMetrics(data.live_scores);
              }
              setAIState('IDLE');
              if (onTurnComplete) {
                onTurnComplete(data);
              }
            } else if (data.type === 'ERROR' || data.event === 'ERROR') {
              setAIState('IDLE');
            }
          } catch (e) {
            console.warn('Error parsing WS text message', e);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          clearInterval(pingInterval);

          if (reconnectAttemptsRef.current < 5) {
            reconnectAttemptsRef.current += 1;
            setTimeout(connectWS, 3000);
          }
        };

        ws.onerror = () => {
          setWsConnected(false);
        };
      } catch (e) {
        console.warn('WebSocket connection error', e);
      }
    };

    connectWS();

    return () => {
      clearInterval(pingInterval);
      audioQueueRef.current = [];
      isPlayingRef.current = false;
      cleanupCurrentAudio();
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [interviewId, enqueueAudioResponse, cleanupCurrentAudio, setWsConnected, setLatencyMs, setAIState, addTranscriptEntry, updateMetrics]);

  const sendEvent = (eventData: object) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(eventData));
    }
  };

  const sendAudioChunk = (chunk: Blob) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      if (chunk && chunk.size > 0) {
        wsRef.current.send(chunk);
      }
    }
  };

  const endCandidateSpeech = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'END_CANDIDATE_SPEECH',
          event: 'END_CANDIDATE_SPEECH',
        })
      );
    }
  };

  return {
    sendEvent,
    sendAudioChunk,
    endCandidateSpeech,
    wsRef,
  };
}
