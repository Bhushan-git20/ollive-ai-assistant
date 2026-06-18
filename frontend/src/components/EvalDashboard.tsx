"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Activity, ShieldAlert, Cpu, Zap } from "lucide-react";
import { motion } from "framer-motion";

export default function EvalDashboard() {
  const [stats, setStats] = useState<any[]>([]);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/stats");
        if (res.ok) {
          const data = await res.json();
          // The API returns an array of stats objects directly
          const statsArray = data.stats.map((row: any) => ({
            model: row.model,
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

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        {[
          { title: "Total Requests", value: "60", icon: Activity, color: "text-blue-400" },
          { title: "Avg Latency", value: "580ms", icon: Zap, color: "text-yellow-400" },
          { title: "Total Tokens", value: "16.2k", icon: Cpu, color: "text-purple-400" },
          { title: "Guardrail Blocks", value: "2", icon: ShieldAlert, color: "text-destructive" },
        ].map((stat, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
          >
            <Card className="p-4 bg-card/40 backdrop-blur border-border/50">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-muted-foreground">{stat.title}</span>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
              <div className="text-2xl font-bold">{stat.value}</div>
            </Card>
          </motion.div>
        ))}
      </div>

      <Card className="bg-card/40 backdrop-blur border-border/50 overflow-hidden">
        <div className="p-6 border-b border-border/50">
          <h3 className="text-lg font-semibold tracking-tight">Model Performance Analytics</h3>
          <p className="text-sm text-muted-foreground">Aggregated metrics from the SQLite observability logger.</p>
        </div>
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/30">
              <TableHead>Model</TableHead>
              <TableHead className="text-right">Requests</TableHead>
              <TableHead className="text-right">Avg Latency</TableHead>
              <TableHead className="text-right">Total Tokens</TableHead>
              <TableHead className="text-right">Guardrail Hits</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {stats.map((row, i) => (
              <TableRow key={i} className="hover:bg-muted/20 transition-colors">
                <TableCell className="font-medium flex items-center gap-2">
                  <div className={`h-2 w-2 rounded-full ${row.model.includes("gemini") ? "bg-blue-500" : "bg-green-500"}`} />
                  {row.model}
                </TableCell>
                <TableCell className="text-right">{row.requests}</TableCell>
                <TableCell className="text-right font-mono text-xs">{row.latency}ms</TableCell>
                <TableCell className="text-right font-mono text-xs">{row.tokens.toLocaleString()}</TableCell>
                <TableCell className="text-right">
                  {row.blocked > 0 ? (
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-destructive/10 text-destructive">
                      {row.blocked}
                    </span>
                  ) : (
                    <span className="text-muted-foreground">-</span>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
