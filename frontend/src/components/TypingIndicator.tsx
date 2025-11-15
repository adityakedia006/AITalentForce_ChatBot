import { Bot } from "lucide-react";

const TypingIndicator = () => {
  return (
    <div className="flex gap-3 w-full animate-fade-in">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-primary flex items-center justify-center shadow-chat">
        <Bot className="w-5 h-5 text-white" />
      </div>
      
      <div className="bg-card text-card-foreground rounded-2xl rounded-tl-sm px-4 py-3 shadow-chat">
        <div className="flex gap-1 items-center">
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: "0ms" }} />
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: "150ms" }} />
          <div className="w-2 h-2 rounded-full bg-primary animate-pulse-soft" style={{ animationDelay: "300ms" }} />
        </div>
      </div>
    </div>
  );
};

export default TypingIndicator;
