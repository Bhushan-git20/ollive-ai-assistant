"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, ShieldAlert, Wrench } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface Message {
  role: "user" | "assistant";
  content: string;
  latency?: number;
  tokens?: number;
  tool_used?: string | null;
  guardrail_triggered?: boolean;
}

export default function ChatInterface({ activeModel }: { activeModel: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Hardcoded session ID for simplicity
  const sessionId = "session_123";

  // Load history on mount or model change
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/history/${sessionId}?model=${activeModel}`);
        if (res.ok) {
          const data = await res.json();
          // Transform history to match Message interface
          const formatted = data.history.map((msg: any) => ({
            role: msg.role,
            content: msg.content
          }));
          setMessages(formatted);
        }
      } catch (err) {
        console.error("Failed to load history", err);
      }
    };
    fetchHistory();
  }, [activeModel]);

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          model: activeModel,
          message: userMessage.content
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setMessages((prev) => [...prev, data]);
      } else {
        setMessages((prev) => [...prev, { role: "assistant", content: "Error connecting to backend." }]);
      }
    } catch (error) {
      console.error(error);
      setMessages((prev) => [...prev, { role: "assistant", content: "Failed to fetch from backend." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-card/30 border border-border/50 rounded-2xl overflow-hidden shadow-sm">
      <div className="flex-1 p-6 overflow-y-auto" ref={scrollRef}>
        <div className="space-y-6 pb-4">
          {messages.length === 0 && (
            <div className="h-[40vh] flex flex-col items-center justify-center text-muted-foreground opacity-60">
              <Bot className="h-12 w-12 mb-4" />
              <p>Ask {activeModel} anything...</p>
            </div>
          )}

          <AnimatePresence>
            {messages.map((msg, i) => (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
                key={i}
              >
                <div className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                  msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted text-foreground"
                }`}>
                  {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                </div>
                
                <div className={`flex flex-col max-w-[80%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                  <div className={`px-5 py-3.5 rounded-2xl ${
                    msg.role === "user" 
                      ? "bg-primary text-primary-foreground rounded-tr-sm" 
                      : msg.guardrail_triggered 
                        ? "bg-destructive/10 text-destructive border border-destructive/20 rounded-tl-sm"
                        : "bg-muted/50 border border-border/50 rounded-tl-sm"
                  }`}>
                    {msg.content}
                  </div>
                  
                  {/* Metadata tags */}
                  {msg.role === "assistant" && (
                    <div className="flex flex-wrap gap-2 mt-2 ml-1">
                      {msg.latency && (
                        <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                          ⏱ {msg.latency.toFixed(0)}ms
                        </span>
                      )}
                      {msg.tokens && (
                        <span className="text-[10px] text-muted-foreground bg-muted px-2 py-0.5 rounded-full">
                          {msg.tokens} tokens
                        </span>
                      )}
                      {msg.tool_used && (
                        <span className="text-[10px] text-blue-400 bg-blue-500/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <Wrench className="h-3 w-3" /> {msg.tool_used}
                        </span>
                      )}
                      {msg.guardrail_triggered && (
                        <span className="text-[10px] text-destructive bg-destructive/10 px-2 py-0.5 rounded-full flex items-center gap-1">
                          <ShieldAlert className="h-3 w-3" /> Blocked
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {isLoading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
              <div className="h-8 w-8 rounded-full bg-muted flex items-center justify-center shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="px-5 py-4 rounded-2xl bg-muted/50 border border-border/50 rounded-tl-sm flex items-center gap-1">
                <span className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce" />
                <span className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce [animation-delay:-0.15s]" />
                <span className="w-2 h-2 bg-foreground/30 rounded-full animate-bounce [animation-delay:-0.3s]" />
              </div>
            </motion.div>
          )}
        </div>
      </div>

      <div className="p-4 bg-background/50 backdrop-blur-sm border-t border-border/50">
        <div className="relative flex items-center">
          <Textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSubmit();
              }
            }}
            placeholder="Send a message..."
            className="min-h-[60px] max-h-[200px] pr-14 resize-none rounded-xl border-muted-foreground/20 focus-visible:ring-primary/30"
          />
          <Button 
            size="icon" 
            className="absolute right-2 bottom-2 h-10 w-10 rounded-lg transition-transform active:scale-95"
            disabled={!input.trim() || isLoading}
            onClick={handleSubmit}
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
        <p className="text-center text-[10px] text-muted-foreground mt-3">
          Ollive AI can make mistakes. Consider verifying important information.
        </p>
      </div>
    </div>
  );
}
