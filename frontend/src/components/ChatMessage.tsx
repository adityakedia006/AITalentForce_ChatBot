import { Bot, User, Volume2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { textToSpeech } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

const ChatMessage = ({ role, content }: ChatMessageProps) => {
  const isBot = role === "assistant";
  const [speaking, setSpeaking] = useState(false);
  const { toast } = useToast();

  const handleSpeak = async () => {
    if (!content || speaking) return;
    try {
      setSpeaking(true);
      const blob = await textToSpeech(content);
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setSpeaking(false);
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        setSpeaking(false);
      };
      await audio.play();
    } catch (e: any) {
      console.error("TTS error", e);
      toast({
        title: "Text-to-Speech failed",
        description: e?.message || "Unable to synthesize speech.",
        variant: "destructive",
      });
      setSpeaking(false);
    }
  };

  return (
    <div
      className={cn(
        "flex gap-3 w-full animate-slide-up",
        isBot ? "justify-start" : "justify-end"
      )}
    >
      {isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center shadow-chat">
          <Bot className="w-5 h-5 text-white" />
        </div>
      )}
      
      <div
        className={cn(
          "max-w-[70%] rounded-2xl px-4 py-3 shadow-chat",
          isBot
            ? "bg-card text-card-foreground rounded-tl-sm"
            : "bg-gradient-primary text-white rounded-tr-sm"
        )}
      >
        <div className={cn("flex items-start gap-2")}
        >
          <p className="text-sm leading-relaxed whitespace-pre-wrap flex-1">{content}</p>
          {isBot && (
            <button
              onClick={handleSpeak}
              title={speaking ? "Playing..." : "Play audio"}
              className={cn(
                "ml-1 rounded-full p-1.5 transition-colors",
                speaking ? "opacity-60 cursor-not-allowed" : "hover:bg-muted"
              )}
              disabled={speaking}
              aria-label="Speak message"
            >
              {speaking ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Volume2 className="w-4 h-4" />
              )}
            </button>
          )}
        </div>
      </div>

      {!isBot && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-accent flex items-center justify-center shadow-chat">
          <User className="w-5 h-5 text-white" />
        </div>
      )}
    </div>
  );
};

export default ChatMessage;
