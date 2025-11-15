import { useState, useRef, useEffect } from "react";
import { Download, MessageSquare, Bot } from "lucide-react";
import ChatMessage from "@/components/ChatMessage";
import TypingIndicator from "@/components/TypingIndicator";
import ChatInput from "@/components/ChatInput";
import RecordingModal from "@/components/RecordingModal";
import ThemeToggle from "@/components/ThemeToggle";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { sendChatMessage, assist, ChatMessage as ApiChatMessage, translateText, getWeather, WeatherResponse } from "@/lib/api";
import { t } from "@/lib/i18n";

interface Message {
  role: "user" | "assistant";
  content: string; // canonical English content
  ja?: string; // cached Japanese translation for display
}

const Index = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: "Hello! I'm your AI assistant. How can I help you today?"
    }
  ]);
  const [isTyping, setIsTyping] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [uiLanguage, setUiLanguage] = useState<"en" | "ja">("en");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const processingControllerRef = useRef<AbortController | null>(null);
  const { toast } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // naive weather intent + location detector
  const maybeExtractWeatherLocation = (text: string): string | null => {
    const lowered = text.toLowerCase();
    const hasWeather = /(weather|temperature|forecast|climate|rain|sunny|cloudy)/i.test(text);
    if (!hasWeather) return null;
    // look for "in <one|two words>" or "at/for <one|two words>"
    const m = lowered.match(/\b(?:in|at|for)\s+([\p{L}.'-]+(?:\s+[\p{L}.'-]+)?)\b/u);
    if (m && m[1]) {
      return m[1].replace(/[?.!,;]+$/g, "").trim();
    }
    return null;
  };

  const formatWeatherForLLM = (w: WeatherResponse) =>
    `Location: ${w.location}, Temperature: ${w.temperature}°C, ` +
    `Condition: ${(w as any).weather_description || (w as any).description || "Unknown"}, ` +
    `Wind Speed: ${w.wind_speed ?? "NA"} km/h, Humidity: ${w.humidity ?? "NA"}%`;

  const handleSendMessage = async (content: string) => {
    const userMessage: Message = { role: "user", content };
    setMessages(prev => [...prev, userMessage]);
    setIsTyping(true);

    try {
      let weatherContext: string | undefined;
      const loc = maybeExtractWeatherLocation(content);
      if (loc) {
        try {
          const w = await getWeather(loc);
          weatherContext = formatWeatherForLLM(w);
        } catch {
          // ignore if weather fetch fails; fall back to normal chat
        }
      }

      const augmented = weatherContext
        ? `${content}\n\n[Weather Information: ${weatherContext}]`
        : content;

      const data = await sendChatMessage(
        augmented,
        messages.map(m => ({ role: m.role, content: m.content }))
      );
      
      const assistantEn = data.response;
      let assistantJa: string | undefined = undefined;
      if (uiLanguage === "ja") {
        try {
          const t = await translateText({ text: assistantEn, target_lang: "ja" });
          assistantJa = t.translated_text;
        } catch (e) {
          console.warn("Translation failed:", e);
        }
      }

      const assistantMessage: Message = { role: "assistant", content: assistantEn, ja: assistantJa };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error sending message:", error);
      toast({
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to send message. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsTyping(false);
    }
  };

  const handleSendAudio = async (audioBlob: Blob) => {
    setIsProcessingAudio(true);
    setIsTyping(true);
    // Create an AbortController to allow canceling the processing request
    const controller = new AbortController();
    processingControllerRef.current = controller;

    try {
      const data = await assist({
        audioBlob,
        conversationHistory: messages.map(m => ({ role: m.role, content: m.content })),
        signal: controller.signal,
      });
      
      setIsProcessingAudio(false);
      processingControllerRef.current = null;
      
      if (data.transcribed_text) {
        const userMessage: Message = { role: "user", content: data.transcribed_text };
        setMessages(prev => [...prev, userMessage]);
      }

      const assistantEn = data.response;
      let assistantJa: string | undefined = undefined;
      if (uiLanguage === "ja") {
        try {
          const t = await translateText({ text: assistantEn, target_lang: "ja" });
          assistantJa = t.translated_text;
        } catch (e) {
          console.warn("Translation failed:", e);
        }
      }
      const assistantMessage: Message = { role: "assistant", content: assistantEn, ja: assistantJa };
      setMessages(prev => [...prev, assistantMessage]);
      
      toast({
        title: t("toast.audioProcessed.title", uiLanguage),
        description: t("toast.audioProcessed.desc", uiLanguage),
      });
    } catch (error: any) {
      // If the request was aborted, silently reset state without showing an error
      if (error?.name === "AbortError") {
        setIsProcessingAudio(false);
        processingControllerRef.current = null;
      } else {
        console.error("Error processing audio:", error);
        setIsProcessingAudio(false);
        processingControllerRef.current = null;
        toast({
          title: t("toast.error.title", uiLanguage),
          description: error instanceof Error ? error.message : t("toast.error.generic", uiLanguage),
          variant: "destructive",
        });
      }
    } finally {
      setIsTyping(false);
    }
  };

  const handleCancelProcessing = () => {
    if (processingControllerRef.current) {
      processingControllerRef.current.abort();
    }
    setIsProcessingAudio(false);
    setIsTyping(false);
  };

  const handleDownloadHistory = () => {
    const dataStr = JSON.stringify(messages, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `chat-history-${new Date().toISOString()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    toast({
      title: "Success",
      description: "Chat history downloaded successfully!",
    });
  };

  return (
    <div className="min-h-screen bg-gradient-bg flex flex-col">
      {/* Header */}
      <header className="bg-card/80 backdrop-blur-sm border-b border-border sticky top-0 z-10 shadow-chat">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-primary flex items-center justify-center shadow-glow">
              <MessageSquare className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-foreground">{t("app.title", uiLanguage)}</h1>
              <p className="text-sm text-muted-foreground">{t("app.subtitle", uiLanguage)}</p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <ThemeToggle />
            <Button
              onClick={async () => {
                const next = uiLanguage === "en" ? "ja" : "en";
                setUiLanguage(next);
                if (next === "ja") {
                  const current = [...messages];
                  const updated: Message[] = [];
                  for (const m of current) {
                    if (m.ja || !m.content) { updated.push(m); continue; }
                    try {
                      const t = await translateText({ text: m.content, target_lang: "ja" });
                      updated.push({ ...m, ja: t.translated_text });
                    } catch {
                      updated.push(m);
                    }
                  }
                  setMessages(updated);
                }
              }}
              variant="outline"
              size="sm"
              className="gap-2 rounded-xl"
              title="Toggle chat language"
            >
              {uiLanguage === "en" ? "EN" : "日本語"}
            </Button>
            <Button
              onClick={handleDownloadHistory}
              variant="outline"
              size="sm"
              className="gap-2 rounded-xl"
            >
              <Download className="w-4 h-4" />
              {t("download", uiLanguage)}
            </Button>
          </div>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.map((message, index) => (
            <ChatMessage
              key={index}
              role={message.role}
              content={uiLanguage === "en" ? message.content : (message.ja || message.content)}
            />
          ))}
          
          {isProcessingAudio && (
            <div className="flex gap-3 w-full animate-slide-up justify-start">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center shadow-chat">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-card text-card-foreground rounded-2xl rounded-tl-sm px-4 py-3 shadow-chat flex items-center gap-3">
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <span>{t("processingAudio", uiLanguage)}</span>
                  <div className="flex gap-1">
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: "0ms" }} />
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: "150ms" }} />
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: "300ms" }} />
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  className="rounded-xl"
                  onClick={handleCancelProcessing}
                >
                  {t("stop", uiLanguage)}
                </Button>
              </div>
            </div>
          )}
          
          {isTyping && !isProcessingAudio && <TypingIndicator />}
          
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="bg-gradient-bg border-t border-border">
        <ChatInput
          onSendMessage={handleSendMessage}
          onSendAudio={handleSendAudio}
          disabled={isTyping || isProcessingAudio}
          isRecording={isRecording}
          onRecordingChange={setIsRecording}
          isProcessing={isProcessingAudio}
          onCancelProcessing={handleCancelProcessing}
          lang={uiLanguage}
        />
      </div>

      {/* Recording Modal */}
      {isRecording && <RecordingModal onStop={() => setIsRecording(false)} />}
    </div>
  );
};

export default Index;

