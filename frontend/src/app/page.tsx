"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import { Bot, MessageSquare, Scale, BarChart3, Settings2, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import ChatInterface from "@/components/ChatInterface";
import CompareInterface from "@/components/CompareInterface";
import EvalDashboard from "@/components/EvalDashboard";

export default function Home() {
  const [activeModel, setActiveModel] = useState("gemini-flash-lite-latest");

  const handleClearHistory = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/history/session_123?model=${activeModel}`, {
        method: "DELETE"
      });
      if (res.ok) {
        console.log("Cleared history for", activeModel);
        // We could also trigger a reload or context refresh here
        window.location.reload(); // Simple way to refresh the chat UI state
      }
    } catch (error) {
      console.error("Failed to clear history", error);
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card/50 backdrop-blur-xl flex flex-col p-4">
        <div className="flex items-center gap-2 mb-8 px-2">
          <Bot className="h-6 w-6 text-primary" />
          <h1 className="font-semibold text-lg tracking-tight">Ollive AI</h1>
        </div>

        <div className="space-y-6 flex-1">
          <div className="space-y-3">
            <h2 className="text-xs font-medium text-muted-foreground uppercase tracking-wider px-2">
              Active Model
            </h2>
            <div className="flex flex-col gap-2">
              <button
                onClick={() => setActiveModel("gemini-flash-lite-latest")}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                  activeModel === "gemini-flash-lite-latest"
                    ? "bg-primary/15 text-primary font-medium"
                    : "hover:bg-muted text-muted-foreground"
                }`}
              >
                <div className="h-2 w-2 rounded-full bg-blue-500" />
                Gemini Flash
              </button>
              <button
                onClick={() => setActiveModel("qwen2.5-0.5B")}
                className={`flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all duration-200 ${
                  activeModel === "qwen2.5-0.5B"
                    ? "bg-primary/15 text-primary font-medium"
                    : "hover:bg-muted text-muted-foreground"
                }`}
              >
                <div className="h-2 w-2 rounded-full bg-green-500" />
                Qwen 2.5 (OSS)
              </button>
            </div>
          </div>

          <div className="pt-4 border-t border-border">
            <Button
              variant="outline"
              className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={handleClearHistory}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Clear History
            </Button>
          </div>
        </div>

        <div className="mt-auto pt-4 border-t border-border">
          <div className="px-2 py-3 bg-muted/50 rounded-lg text-xs text-muted-foreground space-y-1">
            <p className="flex items-center gap-1.5"><Settings2 className="h-3 w-3"/> Tools Active</p>
            <p>• Calculator</p>
            <p>• Datetime</p>
            <p>• Guardrails</p>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0">
        <Tabs defaultValue="chat" className="flex-1 flex flex-col w-full h-full">
          <div className="px-8 pt-6 pb-2 border-b border-border/50 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10 sticky top-0">
            <TabsList className="bg-muted/50">
              <TabsTrigger value="chat" className="gap-2">
                <MessageSquare className="h-4 w-4" /> Chat
              </TabsTrigger>
              <TabsTrigger value="compare" className="gap-2">
                <Scale className="h-4 w-4" /> Compare
              </TabsTrigger>
              <TabsTrigger value="eval" className="gap-2">
                <BarChart3 className="h-4 w-4" /> Eval
              </TabsTrigger>
            </TabsList>
          </div>

          <div className="flex-1 overflow-y-auto p-8">
            <div className="max-w-4xl mx-auto h-full">
              <TabsContent value="chat" className="h-full mt-0 outline-none">
                <ChatInterface activeModel={activeModel} />
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
