import React, { useRef, useEffect } from 'react';

export interface WaveformVisualizerProps {
  micLevel: number; // 0 to 100
  isActive?: boolean;
  width?: number;
  height?: number;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  micLevel,
  isActive = true,
  width = 160,
  height = 36,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;
    const barCount = 18;
    const barWidth = Math.floor(width / barCount) - 2;

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      for (let i = 0; i < barCount; i++) {
        // Compute pseudo-FFT bar height based on mic level & sinewave frequency
        const frequencyMultiplier = Math.sin((i / barCount) * Math.PI + Date.now() / 200);
        const targetHeight = isActive
          ? Math.max(4, Math.min(height, (micLevel / 100) * height * (0.4 + 0.6 * Math.abs(frequencyMultiplier))))
          : 4;

        const x = i * (barWidth + 2);
        const y = (height - targetHeight) / 2;

        const gradient = ctx.createLinearGradient(0, 0, 0, height);
        if (micLevel > 30) {
          gradient.addColorStop(0, '#10b981'); // emerald
          gradient.addColorStop(1, '#059669');
        } else {
          gradient.addColorStop(0, '#818cf8'); // indigo
          gradient.addColorStop(1, '#4f46e5');
        }

        ctx.fillStyle = gradient;
        ctx.beginPath();
        ctx.roundRect(x, y, barWidth, targetHeight, 2);
        ctx.fill();
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [micLevel, isActive, width, height]);

  return (
    <div className="flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-slate-950 border border-slate-800 shadow-inner">
      <canvas ref={canvasRef} width={width} height={height} className="block" />
      <span className="text-[10px] font-mono font-bold text-slate-400 min-w-[28px]">
        {isActive ? `${micLevel}%` : 'OFF'}
      </span>
    </div>
  );
};
