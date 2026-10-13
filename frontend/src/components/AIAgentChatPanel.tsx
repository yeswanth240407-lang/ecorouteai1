"use client";

import React, { useState, useRef, useEffect } from "react";
import { Bot, Send, Sparkles, ChevronDown, ChevronUp, User, CornerDownLeft, Loader2 } from "lucide-react";

interface ThoughtStep {
  agent: string;
  avatar: string;
  thought: string;
}

interface ChatMessage {
  id: string;
  sender: "user" | "agent";
  text: string;
  thoughtChain?: ThoughtStep[];
  timestamp: string;
}

interface AIAgentChatPanelProps {
  scenario: any;
  currentPriority: string;
  trafficLevel: number;
  weather: string;
  onApplyNewPlan: (newScenario?: any, newResult?: any, newPriority?: string) => void;
}

export default function AIAgentChatPanel({
  scenario,
  currentPriority,
  trafficLevel,
  weather,
  onApplyNewPlan,
}: AIAgentChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "init-1",
      sender: "agent",
      text: "Hello! I am **Eco RouteAI**, your autonomous logistics dispatch agent. I coordinate a network of specialized sub-agents: **Data Agent**, **OR-Tools Planner**, **GLEC Emissions Agent**, and **Decision Agent**.\n\nYou can chat with me in plain English to alter routes, add stops, simulate disruptions, or ask trade-off questions!",
      thoughtChain: [
        {
          agent: "Orchestrator Agent",
          avatar: "🧠",
          thought: "Initialized LangGraph multi-agent loop with active Indian fleet models.",
        },
      ],
      timestamp: "Just now",
    },
  ]);

  const [input, setInput] = useState("");
  const [isThinking, setIsThinking] = useState(false);
  const [expandedThoughts, setExpandedThoughts] = useState<Record<string, boolean>>({ "init-1": true });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  const handleSend = async (messageText?: string) => {
    const textToSend = messageText || input;
    if (!textToSend.trim() || isThinking || !scenario) return;

    const userMsgId = `user-${Date.now()}`;
    const userMsg: ChatMessage = {
      id: userMsgId,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsThinking(true);

    try {
      let res;
      try {
        res = await fetch("/api/routes/agent-chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: textToSend,
            scenario,
            current_priority: currentPriority,
            traffic_level: trafficLevel,
            weather: weather,
          }),
        });
      } catch (directErr) {
        const backendBase = process.env.NEXT_PUBLIC_BACKEND_URL || "https://ecoroute-backend-bsi5.onrender.com";
        res = await fetch(`${backendBase}/api/routes/agent-chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            message: textToSend,
            scenario,
            current_priority: currentPriority,
            traffic_level: trafficLevel,
            weather: weather,
          }),
        });
      }

      if (res && res.ok) {
        const data = await res.json();
        const agentMsgId = `agent-${Date.now()}`;
        const agentMsg: ChatMessage = {
          id: agentMsgId,
          sender: "agent",
          text: data.reply,
          thoughtChain: data.thought_chain,
          timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        };

        setMessages((prev) => [...prev, agentMsg]);
        setExpandedThoughts((prev) => ({ ...prev, [agentMsgId]: true }));

        // If the agent took an action that updated the route or scenario, apply it live!
        if (data.optimization_result || data.new_scenario) {
          onApplyNewPlan(
            data.new_scenario || scenario,
            data.optimization_result,
            data.optimization_result?.priority || currentPriority
          );
        }
      } else {
        throw new Error("Agent failed to respond");
      }
    } catch (e: any) {
      const errorMsg: ChatMessage = {
        id: `err-${Date.now()}`,
        sender: "agent",
        text: "I encountered a processing issue contacting the sub-agents. Please check backend connection.",
        timestamp: "Now",
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsThinking(false);
    }
  };

  const toggleThought = (id: string) => {
    setExpandedThoughts((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const quickPrompts = [
    "Switch to Madurai",
    "Switch to Patna",
    "Switch to Surat",
    "Switch to Varanasi",
    "Switch to Guwahati",
    "Switch to Amritsar",
    "Switch to Bhubaneswar",
    "Optimize for greenest emissions",
    "Simulate heavy monsoon rain",
    "Switch to fastest route",
    "Add urgent delivery to Indiranagar (50 kg)",
    "Switch to Chennai Hub",
  ];

  return (
    <div className="flex flex-col h-[520px] bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* Copilot Header */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700/80 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center text-white shadow-md shadow-emerald-500/20">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="font-semibold text-xs text-white flex items-center space-x-1.5">
              <span>Autonomous Dispatch Agent</span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 font-medium px-1.5 py-0.2 rounded-full">Gemini</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            </div>
            <p className="text-[10px] text-slate-400">Google Gemini AI Fleet Orchestrator</p>
          </div>
        </div>
        <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded-full font-mono">
          LangGraph Active
        </span>
      </div>

      {/* Message Stream */}
      <div className="flex-1 p-4 overflow-y-auto space-y-4 text-xs scrollbar-thin scrollbar-thumb-slate-800">
        {messages.map((m) => {
          const isUser = m.sender === "user";
          return (
            <div
              key={m.id}
              className={`flex flex-col ${isUser ? "items-end" : "items-start"}`}
            >
              <div className="flex items-center space-x-1.5 mb-1 px-1">
                {isUser ? (
                  <>
                    <span className="text-[10px] text-slate-500">{m.timestamp}</span>
                    <span className="text-[11px] font-semibold text-slate-300">You (Dispatcher)</span>
                    <User className="w-3 h-3 text-slate-400" />
                  </>
                ) : (
                  <>
                    <Bot className="w-3 h-3 text-emerald-400" />
                    <span className="text-[11px] font-semibold text-emerald-400">Eco RouteAI</span>
                    <span className="text-[10px] text-slate-500">{m.timestamp}</span>
                  </>
                )}
              </div>

              <div
                className={`max-w-[85%] rounded-2xl p-3.5 leading-relaxed ${
                  isUser
                    ? "bg-emerald-600 text-white rounded-tr-none shadow-md"
                    : "bg-slate-950/80 border border-slate-800 text-slate-200 rounded-tl-none shadow-md"
                }`}
              >
                {/* Agent Thought Chain Drawer */}
                {!isUser && m.thoughtChain && m.thoughtChain.length > 0 && (
                  <div className="mb-2.5 pb-2.5 border-b border-slate-800/80">
                    <button
                      onClick={() => toggleThought(m.id)}
                      className="w-full flex items-center justify-between text-[11px] font-medium text-emerald-400/90 hover:text-emerald-300 transition-colors"
                    >
                      <div className="flex items-center space-x-1.5">
                        <Sparkles className="w-3 h-3 text-emerald-400" />
                        <span>Sub-Agent Reasoning Chain ({m.thoughtChain.length} steps)</span>
                      </div>
                      {expandedThoughts[m.id] ? (
                        <ChevronUp className="w-3.5 h-3.5" />
                      ) : (
                        <ChevronDown className="w-3.5 h-3.5" />
                      )}
                    </button>

                    {expandedThoughts[m.id] && (
                      <div className="mt-2 space-y-1.5 pl-1 font-mono text-[10px] border-l-2 border-emerald-500/40">
                        {m.thoughtChain.map((step, sIdx) => (
                          <div key={sIdx} className="pl-2">
                            <span className="font-semibold text-emerald-300">
                              {step.avatar} {step.agent}:
                            </span>{" "}
                            <span className="text-slate-400">{step.thought}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div className="whitespace-pre-line text-xs">{m.text}</div>
              </div>
            </div>
          );
        })}

        {/* Typing / Agent Solving Indicator */}
        {isThinking && (
          <div className="flex items-start space-x-2">
            <div className="w-6 h-6 rounded-full bg-slate-800 flex items-center justify-center text-emerald-400">
              <Bot className="w-3.5 h-3.5" />
            </div>
            <div className="bg-slate-950 border border-slate-800 rounded-2xl p-3 text-xs text-slate-400 flex items-center space-x-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" />
              <span>Agents parsing instruction, solving OR-Tools & checking GLEC...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="px-3 py-2 bg-slate-950/60 border-t border-slate-800/60 flex items-center space-x-1.5 overflow-x-auto no-scrollbar">
        <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider shrink-0 mr-1">
          Suggestions:
        </span>
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            disabled={isThinking}
            className="text-[11px] whitespace-nowrap bg-slate-800/80 hover:bg-slate-800 hover:text-white border border-slate-700/60 text-slate-300 px-2.5 py-1 rounded-full transition-all disabled:opacity-50 shrink-0"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Chat Input Bar */}
      <div className="p-3 bg-slate-900 border-t border-slate-800 flex items-center space-x-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder="Instruct the AI Agent (e.g. 'Add a stop at Indiranagar 50kg')..."
          disabled={isThinking}
          className="flex-1 bg-slate-950 border border-slate-800 focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-500 outline-none transition-all"
        />
        <button
          onClick={() => handleSend()}
          disabled={!input.trim() || isThinking}
          className="p-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-md shadow-emerald-500/20"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
