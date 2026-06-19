"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Bot, MessageSquare, Scale, BarChart3, Settings2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import ChatInterface from "@/components/ChatInterface";
import CompareInterface from "@/components/CompareInterface";
import EvalDashboard from "@/components/EvalDashboard";
import { ThemeToggle } from "@/components/ThemeToggle";
import { Textarea } from "@/components/ui/textarea";

export default function Home() {
  const [activeModel, setActiveModel] = useState("gemini-flash-lite-latest");
  const [systemPrompt, setSystemPrompt] = useState("");

  const handleClearHistory = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/history/session_123?model=${activeModel}`, {
        method: "DELETE"
      });
      if (res.ok) {
        window.location.reload(); 
      }
    } catch (error) {
      console.error("Failed to clear history", error);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card flex flex-col p-4 shadow-xl z-20">
        <div className="flex items-center gap-2 mb-8 px-2">
          <Bot className="h-6 w-6 text-primary" />
          <h1 className="font-heading text-3xl tracking-widest text-primary uppercase mt-1">Ollive AI</h1>
        </div>

        <div className="space-y-6 flex-1 overflow-y-auto pr-2 custom-scrollbar">
          <div className="space-y-3">
            <h2 className="text-xs font-medium text-yellow-500 uppercase tracking-wider px-2">
              Active Model
            </h2>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => setActiveModel("gemini-flash-lite-latest")}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                  activeModel === "gemini-flash-lite-latest"
                    ? "bg-primary text-primary-foreground font-medium shadow-md"
                    : "hover:bg-muted text-muted-foreground"
                }`}
              >
                <div className="h-2 w-2 rounded-full bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
                Gemini Flash
              </button>
              <button
                onClick={() => setActiveModel("qwen2.5-0.5B")}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                  activeModel === "qwen2.5-0.5B"
                    ? "bg-primary text-primary-foreground font-medium shadow-md"
                    : "hover:bg-muted text-muted-foreground"
                }`}
              >
                <div className="h-2 w-2 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                Qwen 2.5 (OSS)
              </button>
            </div>
          </div>
          
          <div className="space-y-3 pt-4 border-t border-border/30">
             <h2 className="text-xs font-medium text-blue-500 uppercase tracking-wider px-2">
              System Prompt
            </h2>
            <Textarea 
              className="text-xs min-h-[80px] bg-background/50 border-border/50 resize-none"
              placeholder="e.g. You are a helpful assistant..."
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
            />
          </div>

          <div className="pt-4 border-t border-border/30">
            <Button
              variant="outline"
              className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10 border-destructive/20"
              onClick={handleClearHistory}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear History
            </Button>
          </div>
        </div>

        <div className="mt-auto pt-4 border-t border-border/30 space-y-4">
          <div className="px-2 py-3 bg-muted/30 rounded-lg text-xs text-yellow-500 space-y-1 border border-border/50">
            <p className="flex items-center gap-1.5"><Settings2 className="h-3 w-3"/> Tools Active</p>
            <p>• Calculator</p>
            <p>• Datetime</p>
            <p>• Web Search</p>
            <p>• Guardrails</p>
          </div>
          <ThemeToggle />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 bg-background relative">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent pointer-events-none" />
        <Tabs defaultValue="chat" className="flex-1 flex flex-col w-full h-full relative z-10">
          <div className="px-8 pt-6 pb-2 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10 sticky top-0">
            <TabsList className="bg-muted/50">
              <TabsTrigger value="chat" className="gap-2">
                <MessageSquare className="h-4 w-4 text-blue-500" /> Chat
              </TabsTrigger>
              <TabsTrigger value="compare" className="gap-2">
                <Scale className="h-4 w-4 text-purple-500" /> Compare
              </TabsTrigger>
              <TabsTrigger value="eval" className="gap-2">
                <BarChart3 className="h-4 w-4 text-green-500" /> Eval
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto h-full">
              <TabsContent value="chat" className="h-full mt-0 outline-none">
                <ChatInterface activeModel={activeModel} systemPrompt={systemPrompt} />
              </TabsContent>
              <TabsContent value="compare" className="h-full mt-0 outline-none">
                <CompareInterface />
              </TabsContent>
              <TabsContent value="eval" className="h-full mt-0 outline-none">
                <EvalDashboard />
              </TabsContent>
            </div>
          </div>
        </Tabs>
      </main>
    </div>
  );
}
