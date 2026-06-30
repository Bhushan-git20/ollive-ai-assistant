"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Send, Bot, User, ShieldAlert, Wrench, ThumbsUp, ThumbsDown, Copy, Check } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { getApiUrl } from "@/lib/utils";

interface Message {
  id?: number;
  role: "user" | "assistant";
  content: string;
  latency?: number;
  tokens?: number;
  tool_used?: string | null;
  guardrail_triggered?: boolean;
  rating?: number;
}

export default function ChatInterface({ activeModel, systemPrompt }: { activeModel: string, systemPrompt?: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  // Hardcoded session ID for simplicity
  const sessionId = "session_123";

  // Load history on mount or model change
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await fetch(getApiUrl(`/api/history/${sessionId}?model=${activeModel}`));
        if (res.ok) {
          const data = await res.json();
          // Transform history to match Message interface
          const formatted = data.history.map((msg: { id?: number, role: string, content: string, rating?: number }) => ({
            id: msg.id,
            role: msg.role as "user" | "assistant",
            content: msg.content,
            rating: msg.rating
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

  const handleRate = async (messageId: number, rating: number, index: number) => {
    // Optimistic update
    setMessages(prev => {
      const newMsgs = [...prev];
      newMsgs[index] = { ...newMsgs[index], rating };
      return newMsgs;
    });

    try {
      await fetch(getApiUrl(`/api/rate/${messageId}`), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rating })
      });
    } catch (err) {
      console.error("Failed to rate message", err);
    }
  };

  const handleCopy = (content: string, index: number) => {
    navigator.clipboard.writeText(content);
    setCopiedId(index);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleSubmit = async (overrideInput?: string) => {
    const textToSubmit = overrideInput || input;
    if (!textToSubmit.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: textToSubmit };
    
    setMessages((prev) => [...prev, userMessage, { role: "assistant", content: "" }]);
    if (!overrideInput) setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(getApiUrl("/api/chat/stream"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          model: activeModel,
          message: textToSubmit,
          system_prompt: systemPrompt
        })
      });
      
      if (!res.ok) {
        throw new Error("Network response was not ok");
      }

      setIsLoading(false);

      const reader = res.body?.getReader();
      const decoder = new TextDecoder("utf-8");

      if (reader) {
        let done = false;
        while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const dataStr = line.replace('data: ', '');
                try {
                  const data = JSON.parse(dataStr);
                  if (data.error) {
                    setMessages(prev => {
                      const newMsgs = [...prev];
                      newMsgs[newMsgs.length - 1] = { ...newMsgs[newMsgs.length - 1], content: "Error: " + data.error };
                      return newMsgs;
                    });
                    break;
                  }
                  
                  if (data.is_done) {
                     if (data.message_id) {
                       setMessages(prev => {
                         const newMsgs = [...prev];
                         newMsgs[newMsgs.length - 1] = { ...newMsgs[newMsgs.length - 1], id: data.message_id };
                         return newMsgs;
                       });
                     }
                     break;
                  }

                  setMessages(prev => {
                    const newMsgs = [...prev];
                    const currentAssistant = newMsgs[newMsgs.length - 1];
                    newMsgs[newMsgs.length - 1] = {
                      ...currentAssistant,
                      content: currentAssistant.content + data.content,
                      tool_used: data.tool_used || currentAssistant.tool_used,
                    };
                    return newMsgs;
                  });
                } catch (e) {
                  // Ignore JSON parse errors for incomplete chunks
                }
              }
            }
          }
        }
      }
    } catch (error) {
      console.error(error);
      setMessages(prev => {
        const newMsgs = [...prev];
        newMsgs[newMsgs.length - 1] = { ...newMsgs[newMsgs.length - 1], content: "Failed to fetch from backend." };
        return newMsgs;
      });
      setIsLoading(false);
    }
  };

  const allTemplates = [
    "Explain quantum physics simply",
    "Write a Python script for a scraper",
    "What is the date today?",
    "Calculate 24 * 365",
    "How do neural networks work?",
    "Write a haiku about the ocean",
    "What's a good recipe for pancakes?",
    "Translate 'Good morning' to Spanish",
    "Summarize the theory of relativity",
    "Write a SQL query to join two tables"
  ];

  const [displayTemplates, setDisplayTemplates] = useState<string[]>([]);

  useEffect(() => {
    const shuffled = [...allTemplates].sort(() => 0.5 - Math.random());
    setDisplayTemplates(shuffled.slice(0, 4));
  }, [activeModel]);

  return (
    <div className="flex flex-col h-full bg-card border border-border rounded-xl overflow-hidden shadow-lg">
      <div className="flex-1 p-6 overflow-y-auto" ref={scrollRef}>
        <div className="space-y-6 pb-4">
          {messages.length === 0 && (
            <div className="h-[40vh] flex flex-col items-center justify-center text-muted-foreground opacity-60">
              <Bot className="h-12 w-12 mb-4" />
              <p className="font-heading text-2xl tracking-widest text-primary uppercase">Ask {activeModel} anything...</p>
              <div className="grid grid-cols-2 gap-2 mt-6">
                {displayTemplates.map((tpl, idx) => (
                  <button 
                    key={idx}
                    onClick={() => handleSubmit(tpl)}
                    className="px-4 py-2 border border-red-500/50 text-red-500 rounded-lg text-xs font-semibold tracking-wider hover:bg-red-500 hover:text-white transition-colors"
                  >
                    {tpl}
                  </button>
                ))}
              </div>
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
                  <div className={`px-5 py-3.5 rounded-2xl whitespace-pre-wrap ${
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
                    <div className="flex flex-wrap gap-2 mt-2 ml-1 items-center">
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
                      <div className="flex gap-1 ml-2">
                        {msg.id && (
                          <>
                            <button 
                              onClick={() => handleRate(msg.id!, 1, i)}
                              className={`p-1 rounded hover:bg-muted transition-colors ${msg.rating === 1 ? 'text-green-500' : 'text-muted-foreground'}`}
                            >
                              <ThumbsUp className="h-3 w-3" />
                            </button>
                            <button 
                              onClick={() => handleRate(msg.id!, -1, i)}
                              className={`p-1 rounded hover:bg-muted transition-colors ${msg.rating === -1 ? 'text-red-500' : 'text-muted-foreground'}`}
                            >
                              <ThumbsDown className="h-3 w-3" />
                            </button>
                          </>
                        )}
                        <button 
                          onClick={() => handleCopy(msg.content, i)}
                          className="p-1 rounded hover:bg-muted transition-colors text-muted-foreground ml-1"
                        >
                          {copiedId === i ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                        </button>
                      </div>
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

      <div className="p-4 bg-background border-t border-border">
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
            className="min-h-[60px] max-h-[200px] pr-14 resize-none rounded-xl border-border focus-visible:ring-primary font-sans text-sm"
          />
          <Button 
            size="icon" 
            className="absolute right-2 bottom-2 h-10 w-10 rounded-lg transition-all active:scale-95 border border-transparent hover:border-primary hover:bg-transparent hover:text-primary text-primary-foreground bg-primary"
            disabled={!input.trim() || isLoading}
            onClick={() => handleSubmit()}
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
