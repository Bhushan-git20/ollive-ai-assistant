"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Activity, ShieldAlert, Cpu, Zap, Play, Terminal } from "lucide-react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";

export default function EvalDashboard() {
  const [stats, setStats] = useState<{name: string, requests: number, latency: number, tokens: number, blocked: number}[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string>("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/stats");
        if (res.ok) {
          const data = await res.json();
          const statsArray = data.stats.map((row: { model: string, requests: number, avg_latency_ms: number, total_prompt_tokens?: number, total_completion_tokens?: number, guardrail_hits: number }) => ({
            name: row.model,
            requests: row.requests,
            latency: row.avg_latency_ms,
            tokens: (row.total_prompt_tokens || 0) + (row.total_completion_tokens || 0),
            blocked: row.guardrail_hits
          }));
          setStats(statsArray);
        }
      } catch (error) {
        console.error("Failed to fetch stats", error);
      }
    };
    fetchStats();
  }, []);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    const fetchLogs = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/eval/logs");
        if (res.ok) {
          const data = await res.json();
          setLogs(data.logs);
          setIsRunning(data.is_running);
        }
      } catch (err) {
        // ignore
      }
    };

    if (isRunning) {
      interval = setInterval(fetchLogs, 2000);
    } else {
      fetchLogs(); // one last fetch
    }
    return () => clearInterval(interval);
  }, [isRunning]);

  const handleRunEval = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/eval/run", { method: "POST" });
      if (res.ok) {
        setIsRunning(true);
        setLogs("Starting Evaluation Runner...\n");
      }
    } catch (err) {
      console.error("Failed to start eval", err);
    }
  };

  const totalRequests = stats.reduce((acc, curr) => acc + curr.requests, 0);
  const avgLat = stats.length ? Math.round(stats.reduce((acc, curr) => acc + curr.latency, 0) / stats.length) : 0;
  const totalToks = stats.reduce((acc, curr) => acc + curr.tokens, 0);
  const totalBlocks = stats.reduce((acc, curr) => acc + curr.blocked, 0);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-semibold text-yellow-500">Evaluation Dashboard</h2>
        <Button onClick={handleRunEval} disabled={isRunning} className="gap-2 bg-yellow-500 hover:bg-yellow-600 text-black font-bold">
          {isRunning ? <Terminal className="h-4 w-4 animate-pulse" /> : <Play className="h-4 w-4" />}
          {isRunning ? "Running Eval..." : "Run Evaluation Suite"}
        </Button>
      </div>

      <div className="grid grid-cols-4 gap-4">
        {[
          { title: "Total Requests", value: totalRequests.toString(), icon: Activity, color: "text-blue-400" },
          { title: "Avg Latency", value: `${avgLat}ms`, icon: Zap, color: "text-yellow-400" },
          { title: "Total Tokens", value: totalToks.toLocaleString(), icon: Cpu, color: "text-purple-400" },
          { title: "Guardrail Blocks", value: totalBlocks.toString(), icon: ShieldAlert, color: "text-destructive" },
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card className="p-4 bg-card/40 backdrop-blur border-border/50 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">{stat.title}</span>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
              <div className="text-2xl font-bold">{stat.value}</div>
            </Card>
          </motion.div>
        ))}
      </div>

      {(logs || isRunning) && (
        <Card className="bg-black border-border/50 overflow-hidden font-mono text-xs text-green-400 p-4 h-64 overflow-y-auto">
          <pre className="whitespace-pre-wrap">{logs}</pre>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-6">
        <Card className="bg-card/40 backdrop-blur border-border/50 overflow-hidden shadow-sm p-6">
          <h3 className="text-lg font-semibold tracking-tight mb-6 text-yellow-500">Latency Comparison (ms)</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#ef4444' }} className="opacity-70" />
                <YAxis tick={{ fontSize: 12, fill: '#ef4444' }} className="opacity-70" />
                <Tooltip 
                  cursor={{ fill: 'currentColor', opacity: 0.05 }}
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                />
                <Bar dataKey="latency" fill="#eab308" radius={[4, 4, 0, 0]} maxBarSize={60} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card className="bg-card/40 backdrop-blur border-border/50 overflow-hidden shadow-sm p-6">
          <h3 className="text-lg font-semibold tracking-tight mb-6 text-yellow-500">Token Usage Comparison</h3>
          <div className="h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={stats} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="currentColor" className="opacity-10" />
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: '#ef4444' }} className="opacity-70" />
                <YAxis tick={{ fontSize: 12, fill: '#ef4444' }} className="opacity-70" />
                <Tooltip 
                  cursor={{ fill: 'currentColor', opacity: 0.05 }}
                  contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                />
                <Bar dataKey="tokens" fill="#eab308" radius={[4, 4, 0, 0]} maxBarSize={60} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </div>
  );
}
