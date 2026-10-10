"use client";

import React, { useState } from "react";
import { Terminal, ChevronDown, ChevronUp, Bot } from "lucide-react";

interface AgentActivityLogsProps {
  logs: string[];
}

export default function AgentActivityLogs({ logs }: AgentActivityLogsProps) {
  const [isOpen, setIsOpen] = useState(true);

  if (!logs || logs.length === 0) return null;

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-lg">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-2.5 bg-slate-800/60 hover:bg-slate-800 flex items-center justify-between text-xs font-medium text-slate-300 transition-colors"
      >
        <div className="flex items-center space-x-2">
          <Bot className="w-4 h-4 text-emerald-400" />
          <span className="font-semibold text-slate-200">LangGraph Agent Activity Trace</span>
          <span className="bg-emerald-500/20 text-emerald-400 text-[10px] px-1.5 py-0.5 rounded-full font-mono">
            {logs.length} events
          </span>
        </div>
        {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
      </button>

      {isOpen && (
        <div className="p-3 bg-slate-950 font-mono text-[11px] leading-relaxed max-h-48 overflow-y-auto space-y-1.5 scrollbar-thin scrollbar-thumb-slate-800">
          {logs.map((log, idx) => {
            const isData = log.includes("[Data Agent]");
            const isPlanner = log.includes("[Planner Agent]");
            const isEmissions = log.includes("[Emissions Agent]");
            const isDecision = log.includes("[Decision Agent]");
            const isExplainer = log.includes("[Explainer Agent]");

            return (
              <div key={idx} className="flex items-start space-x-2 text-slate-300">
                <span className="text-slate-600 select-none">{String(idx + 1).padStart(2, "0")}</span>
                <span
                  className={
                    isData
                      ? "text-sky-400"
                      : isPlanner
                      ? "text-indigo-400"
                      : isEmissions
                      ? "text-emerald-400 font-semibold"
                      : isDecision
                      ? "text-amber-400 font-semibold"
                      : isExplainer
                      ? "text-purple-400"
                      : "text-slate-400"
                  }
                >
                  {log}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
