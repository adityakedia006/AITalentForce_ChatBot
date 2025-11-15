import { useState, useRef, useEffect } from "react";
import { Send, Mic, Square } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { t } from "@/lib/i18n";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  onSendAudio: (audioBlob: Blob) => void;
  disabled?: boolean;
  isRecording: boolean;
  onRecordingChange: (recording: boolean) => void;
  isProcessing?: boolean;
  onCancelProcessing?: () => void;
  lang?: "en" | "ja";
}

const ChatInput = ({ onSendMessage, onSendAudio, disabled, isRecording, onRecordingChange, isProcessing, onCancelProcessing, lang = "en" }: ChatInputProps) => {
  const [message, setMessage] = useState("");
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 120)}px`;
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !disabled && !isProcessing) {
      onSendMessage(message.trim());
      setMessage("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      
      audioChunksRef.current = [];
      
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };
      
      recorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        onSendAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };
      
      recorder.start();
      setMediaRecorder(recorder);
      onRecordingChange(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      onRecordingChange(false);
      setMediaRecorder(null);
    }
  };

  // If parent turns off recording (e.g., via RecordingModal Stop), ensure we stop the recorder here
  useEffect(() => {
    if (!isRecording && mediaRecorder) {
      try {
        mediaRecorder.stop();
      } catch (_) {
        // no-op
      } finally {
        setMediaRecorder(null);
      }
    }
  }, [isRecording, mediaRecorder]);

  return (
    <form onSubmit={handleSubmit} className="w-full max-w-4xl mx-auto px-4 pb-6">
      <div className="bg-card rounded-2xl shadow-chat-md p-4 border border-border">
        <div className="flex gap-2 items-end">
          <div className="relative flex-1">
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t("placeholder", lang)}
              disabled={disabled || isRecording || !!isProcessing}
              className="min-h-[44px] max-h-[120px] resize-none border-0 focus-visible:ring-0 focus-visible:ring-offset-0 bg-transparent pr-24"
              rows={1}
            />
            {isProcessing && (
              <Badge
                variant="secondary"
                className="absolute left-2 bottom-2 rounded-xl text-[10px] px-2 py-0.5"
              >
                {t("processing", lang)}
              </Badge>
            )}
          </div>
          
          <div className="flex gap-2">
            <Button
              type="button"
              size="icon"
              variant="ghost"
              onClick={isRecording ? stopRecording : startRecording}
              disabled={disabled || !!isProcessing}
              className={cn(
                "h-11 w-11 rounded-xl transition-all",
                isRecording && "bg-destructive text-destructive-foreground animate-pulse-soft hover:bg-destructive/90"
              )}
            >
              {isRecording ? (
                <Square className="h-5 w-5" />
              ) : (
                <Mic className="h-5 w-5" />
              )}
            </Button>
            {isProcessing && (
              <Button
                type="button"
                variant="outline"
                className="h-11 rounded-xl"
                onClick={onCancelProcessing}
              >
                {t("stop", lang)}
              </Button>
            )}
            
            <Button
              type="submit"
              size="icon"
              disabled={!message.trim() || disabled || isRecording || !!isProcessing}
              className="h-11 w-11 rounded-xl bg-gradient-primary hover:opacity-90 transition-opacity"
            >
              <Send className="h-5 w-5" />
            </Button>
          </div>
        </div>
      </div>
    </form>
  );
};

export default ChatInput;
