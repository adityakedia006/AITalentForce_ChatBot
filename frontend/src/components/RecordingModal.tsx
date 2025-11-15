import { useEffect, useState } from "react";
import { Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";

interface RecordingModalProps {
  onStop: () => void;
}

const RecordingModal = ({ onStop }: RecordingModalProps) => {
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setSeconds(prev => prev + 1);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const formatTime = (totalSeconds: number) => {
    const mins = Math.floor(totalSeconds / 60);
    const secs = totalSeconds % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm animate-fade-in">
      <div className="bg-card rounded-3xl shadow-chat-md p-8 max-w-sm w-full mx-4 animate-scale-in border border-border">
        <div className="flex flex-col items-center gap-6">
          {/* Animated Mic Icon */}
          <div className="relative">
            <div className="absolute inset-0 rounded-full bg-destructive/20 animate-ping" />
            <div className="relative w-24 h-24 rounded-full bg-gradient-primary flex items-center justify-center shadow-glow">
              <Mic className="w-12 h-12 text-white animate-pulse-soft" />
            </div>
          </div>

          {/* Recording Status */}
          <div className="text-center space-y-2">
            <h3 className="text-xl font-semibold text-foreground">Recording...</h3>
            <p className="text-sm text-muted-foreground">Speak clearly into your microphone</p>
          </div>

          {/* Timer */}
          <div className="text-5xl font-mono font-bold text-primary tabular-nums">
            {formatTime(seconds)}
          </div>

          {/* Waveform Effect */}
          <div className="flex gap-1 h-12 items-center">
            {[...Array(5)].map((_, i) => (
              <div
                key={i}
                className="w-1 bg-primary rounded-full animate-pulse-soft"
                style={{
                  height: `${20 + Math.random() * 30}px`,
                  animationDelay: `${i * 150}ms`,
                  animationDuration: "0.8s"
                }}
              />
            ))}
          </div>

          {/* Stop Button */}
          <Button
            onClick={onStop}
            size="lg"
            className="w-full gap-2 bg-destructive hover:bg-destructive/90 text-destructive-foreground rounded-xl"
          >
            <Square className="w-5 h-5" />
            Stop Recording
          </Button>
        </div>
      </div>
    </div>
  );
};

export default RecordingModal;
