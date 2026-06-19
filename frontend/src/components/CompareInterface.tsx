"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Send, Scale, Clock, FileText } from "lucide-react";
import { motion } from "framer-motion";

export default function CompareInterface() {
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState<{
    gemini?: { content: string; latency: number; tokens: number };
    qwen?: { content: string; latency: number; tokens: number };
  } | null>(null);

  const handleCompare = async () => {
    if (!input.trim() || isLoading) return;
    setIsLoading(true);
    setResults(null);

    try {
      const res = await fetch("http://localhost:8000/api/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: "session_123",
          message: input
        })
      });
      
      if (res.ok) {
        const data = await res.json();
        setResults({
          gemini: data.gemini,
          qwen: data.qwen
        });
      } else {
        console.error("Error connecting to backend");
      }
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full gap-6">
      <Card className="p-6 bg-card border border-border shadow-lg shrink-0 rounded-xl">
        <div className="flex items-start gap-4">
          <div className="bg-primary/10 p-3 rounded-xl">
            <Scale className="h-6 w-6 text-primary" />
          </div>
          <div className="flex-1">
            <h2 className="font-heading text-3xl tracking-widest uppercase text-primary">Model Comparison</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Send a single prompt and watch how both frontier (Gemini) and open-source (Qwen) models respond.
            </p>
            <div className="relative">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a challenging question..."
                className="min-h-[80px] pr-28 resize-none bg-background/50 border-muted-foreground/20 rounded-xl"
              />
              <Button
                onClick={handleCompare}
                disabled={!input.trim() || isLoading}
                className="absolute right-2 bottom-2 rounded-lg transition-all active:scale-95 border border-transparent hover:border-primary hover:bg-transparent hover:text-primary"
              >
                {isLoading ? "Running..." : "Compare Models"}
                {!isLoading && <Send className="ml-2 h-4 w-4" />}
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {(isLoading || results) && (
        <div className="grid grid-cols-2 gap-6 flex-1 min-h-0">
          {/* Gemini Result */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col h-full bg-blue-500/5 border border-blue-500/20 rounded-2xl overflow-hidden"
          >
            <div className="px-4 py-3 border-b border-blue-500/20 bg-blue-500/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-blue-500" />
                <span className="font-semibold text-blue-400">Gemini Flash Lite</span>
              </div>
              {results?.gemini && (
                <div className="flex gap-3 text-xs text-blue-400/80 font-medium">
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3"/> {results.gemini.latency}ms</span>
                  <span className="flex items-center gap-1"><FileText className="h-3 w-3"/> {results.gemini.tokens} tokens</span>
                </div>
              )}
            </div>
            <div className="p-6 overflow-y-auto">
              {isLoading ? (
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-blue-500/20 rounded w-3/4"></div>
                  <div className="h-4 bg-blue-500/20 rounded w-full"></div>
                  <div className="h-4 bg-blue-500/20 rounded w-5/6"></div>
                </div>
              ) : (
                <div className="text-sm leading-relaxed">{results?.gemini?.content}</div>
              )}
            </div>
          </motion.div>

          {/* Qwen Result */}
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="flex flex-col h-full bg-green-500/5 border border-green-500/20 rounded-2xl overflow-hidden"
          >
            <div className="px-4 py-3 border-b border-green-500/20 bg-green-500/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-green-500" />
                <span className="font-semibold text-green-400">Qwen 2.5 (0.5B)</span>
              </div>
              {results?.qwen && (
                <div className="flex gap-3 text-xs text-green-400/80 font-medium">
                  <span className="flex items-center gap-1"><Clock className="h-3 w-3"/> {results.qwen.latency}ms</span>
                  <span className="flex items-center gap-1"><FileText className="h-3 w-3"/> {results.qwen.tokens} tokens</span>
                </div>
              )}
            </div>
            <div className="p-6 overflow-y-auto">
              {isLoading ? (
                <div className="animate-pulse space-y-3">
                  <div className="h-4 bg-green-500/20 rounded w-full"></div>
                  <div className="h-4 bg-green-500/20 rounded w-4/5"></div>
                  <div className="h-4 bg-green-500/20 rounded w-2/3"></div>
                </div>
              ) : (
                <div className="text-sm leading-relaxed">{results?.qwen?.content}</div>
              )}
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
