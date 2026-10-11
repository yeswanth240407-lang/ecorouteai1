"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  ShieldAlert, Lightbulb, Leaf, RefreshCw, ChevronDown, ChevronUp,
  Zap, AlertTriangle, CheckCircle, TrendingUp, Wind, Clock
} from "lucide-react";

interface Alert {
  id: string;
  severity: string;
  icon: string;
  title: string;
  message: string;
  action: string;
}

interface Recommendation {
  id: string;
  icon: string;
  priority: string;
  title: string;
  detail: string;
  impact: string;
}

interface CarbonForecast {
  co2_saved_today_kg?: number;
  carbon_credits_inr?: number;
  monthly_projection_inr?: number;
  annual_projection_inr?: number;
  ev_vehicles_used?: number;
  diesel_vehicles_replaced?: number;
  standard?: string;
  message: string;
}

interface AdvisoryResult {
  agent_name: string;
  risk_score: number;
  risk_label: string;
  risk_color: string;
  alerts: Alert[];
  recommendations: Recommendation[];
  carbon_forecast: CarbonForecast;
  stats: {
    stops_analysed: number;
    alerts_generated: number;
    recommendations_generated: number;
    weather_risk: string;
    traffic_level: string;
    duration_ms: number;
  };
}

interface AdvisoryAgentPanelProps {
  scenario: any;
  optimizationResult?: any;
}

const SEVERITY_STYLES: Record<string, string> = {
  CRITICAL: "border-red-500/40 bg-red-500/10 text-red-300",
  HIGH:     "border-orange-500/40 bg-orange-500/10 text-orange-300",
  MEDIUM:   "border-yellow-500/40 bg-yellow-500/10 text-yellow-300",
  LOW:      "border-emerald-500/40 bg-emerald-500/10 text-emerald-300",
};

const PRIORITY_DOT: Record<string, string> = {
  HIGH:   "bg-orange-400",
  MEDIUM: "bg-yellow-400",
  LOW:    "bg-emerald-400",
};

export default function AdvisoryAgentPanel({ scenario, optimizationResult }: AdvisoryAgentPanelProps) {
  const [result, setResult]       = useState<AdvisoryResult | null>(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [expanded, setExpanded]   = useState<Record<string, boolean>>({});
  const [lastDepot, setLastDepot] = useState<string>("");

  const fetchAdvisory = useCallback(async () => {
    if (!scenario?.depot) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/routes/advisory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ scenario, optimization_result: optimizationResult ?? null }),
      });
      if (!res.ok) throw new Error("Advisory agent request failed");
      const data: AdvisoryResult = await res.json();
      setResult(data);
    } catch (e: any) {
      setError("Could not reach Advisory Agent. Check backend connection.");
    } finally {
      setLoading(false);
    }
  }, [scenario, optimizationResult]);

  // Auto-fetch when depot changes
  useEffect(() => {
    const depotKey = scenario?.depot?.name + scenario?.depot?.lat;
    if (depotKey !== lastDepot) {
      setLastDepot(depotKey);
      fetchAdvisory();
    }
  }, [scenario?.depot?.name, scenario?.depot?.lat, optimizationResult]);

  const toggle = (id: string) => setExpanded(p => ({ ...p, [id]: !p[id] }));

  // Risk score ring colour
  const ringColor =
    !result ? "text-slate-600" :
    result.risk_score < 25 ? "text-emerald-400" :
    result.risk_score < 55 ? "text-yellow-400"  :
    result.risk_score < 80 ? "text-orange-400"  : "text-red-400";

  return (
    <div className="flex flex-col bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
      {/* ── Header ── */}
      <div className="px-4 py-3 bg-slate-800/80 border-b border-slate-700/80 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-violet-500 to-indigo-400 flex items-center justify-center shadow-md shadow-violet-500/20">
            <ShieldAlert className="w-4 h-4 text-white" />
          </div>
          <div>
            <div className="font-semibold text-xs text-white flex items-center space-x-1.5">
              <span>Predictive Risk &amp; Advisory Agent</span>
              <span className="w-2 h-2 rounded-full bg-violet-400 animate-pulse" />
            </div>
            <p className="text-[10px] text-slate-400">Proactive Smart Alerts · Carbon Credit Forecasting</p>
          </div>
        </div>
        <button
          onClick={fetchAdvisory}
          disabled={loading}
          className="p-1.5 rounded-lg bg-slate-700 hover:bg-slate-600 transition-colors disabled:opacity-50"
          title="Refresh Analysis"
        >
          <RefreshCw className={`w-3.5 h-3.5 text-slate-300 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>

      <div className="flex flex-col gap-3 p-4 overflow-y-auto max-h-[640px]">

        {/* ── Loading ── */}
        {loading && (
          <div className="flex flex-col items-center justify-center py-10 gap-3">
            <div className="w-10 h-10 rounded-full border-2 border-violet-500 border-t-transparent animate-spin" />
            <p className="text-xs text-slate-400">Advisory Agent analysing scenario…</p>
          </div>
        )}

        {/* ── Error ── */}
        {error && !loading && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300">
            {error}
          </div>
        )}

        {/* ── No scenario ── */}
        {!scenario?.depot && !loading && (
          <div className="flex flex-col items-center py-10 gap-2 text-slate-500">
            <ShieldAlert className="w-8 h-8 opacity-30" />
            <p className="text-xs">Load a city scenario to activate the Advisory Agent.</p>
          </div>
        )}

        {result && !loading && (
          <>
            {/* ── Risk Score Card ── */}
            <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-4 flex items-center gap-4">
              <div className="relative w-16 h-16 flex-shrink-0">
                <svg className="w-16 h-16 -rotate-90" viewBox="0 0 64 64">
                  <circle cx="32" cy="32" r="26" fill="none" stroke="#1e293b" strokeWidth="6" />
                  <circle
                    cx="32" cy="32" r="26"
                    fill="none"
                    strokeWidth="6"
                    stroke="currentColor"
                    strokeDasharray={`${(result.risk_score / 100) * 163.4} 163.4`}
                    strokeLinecap="round"
                    className={ringColor}
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className={`text-lg font-bold ${ringColor}`}>{result.risk_score}</span>
                </div>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-400 mb-0.5">Overall Risk Score</p>
                <p className={`font-bold text-sm ${ringColor}`}>{result.risk_label}</p>
                <div className="flex gap-3 mt-1.5 flex-wrap">
                  <span className="text-[10px] text-slate-400">🌦️ {result.stats.weather_risk}</span>
                  <span className="text-[10px] text-slate-400">🚗 {result.stats.traffic_level}</span>
                  <span className="text-[10px] text-slate-400">📍 {result.stats.stops_analysed} stops</span>
                </div>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-[10px] text-slate-500">{result.stats.alerts_generated} alert{result.stats.alerts_generated !== 1 ? "s" : ""}</p>
                <p className="text-[10px] text-slate-500">{result.stats.recommendations_generated} tip{result.stats.recommendations_generated !== 1 ? "s" : ""}</p>
                <p className="text-[10px] text-slate-600 mt-1">{result.stats.duration_ms}ms</p>
              </div>
            </div>

            {/* ── Alerts ── */}
            {result.alerts.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-3 h-3" /> Active Alerts
                </p>
                {result.alerts.map(alert => (
                  <div
                    key={alert.id}
                    className={`rounded-xl border p-3 cursor-pointer ${SEVERITY_STYLES[alert.severity] || SEVERITY_STYLES.LOW}`}
                    onClick={() => toggle(alert.id)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2">
                        <span className="text-base leading-none mt-0.5">{alert.icon}</span>
                        <div>
                          <p className="text-xs font-semibold">{alert.title}</p>
                          {expanded[alert.id] && (
                            <>
                              <p className="text-[11px] opacity-80 mt-1">{alert.message}</p>
                              <div className="mt-2 flex items-center gap-1.5 text-[10px] opacity-70">
                                <Zap className="w-3 h-3" />
                                <span>{alert.action}</span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                      {expanded[alert.id]
                        ? <ChevronUp className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />
                        : <ChevronDown className="w-3.5 h-3.5 flex-shrink-0 opacity-60" />}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ── Recommendations ── */}
            {result.recommendations.length > 0 && (
              <div className="flex flex-col gap-2">
                <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                  <Lightbulb className="w-3 h-3" /> Smart Recommendations
                </p>
                {result.recommendations.map(rec => (
                  <div
                    key={rec.id}
                    className="rounded-xl border border-slate-700 bg-slate-800/50 p-3 cursor-pointer hover:border-slate-600 transition-colors"
                    onClick={() => toggle(rec.id)}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-start gap-2">
                        <span className="text-base leading-none mt-0.5">{rec.icon}</span>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <p className="text-xs font-semibold text-slate-200">{rec.title}</p>
                            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${PRIORITY_DOT[rec.priority] || "bg-slate-500"}`} />
                          </div>
                          {expanded[rec.id] && (
                            <>
                              <p className="text-[11px] text-slate-400 mt-1">{rec.detail}</p>
                              <div className="mt-2 flex items-center gap-1.5 text-[10px] text-emerald-400">
                                <TrendingUp className="w-3 h-3" />
                                <span>{rec.impact}</span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                      {expanded[rec.id]
                        ? <ChevronUp className="w-3.5 h-3.5 flex-shrink-0 text-slate-500" />
                        : <ChevronDown className="w-3.5 h-3.5 flex-shrink-0 text-slate-500" />}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* ── Carbon Credit Forecast ── */}
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-4">
              <p className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1.5 mb-3">
                <Leaf className="w-3 h-3" /> Carbon Credit Forecast
              </p>
              {result.carbon_forecast.co2_saved_today_kg !== undefined ? (
                <div className="grid grid-cols-2 gap-2 mb-3">
                  {[
                    { label: "CO₂ Saved Today",   value: `${result.carbon_forecast.co2_saved_today_kg} kg`,         icon: "🌿" },
                    { label: "Credits (Today)",    value: `₹${result.carbon_forecast.carbon_credits_inr?.toFixed(2)}`, icon: "💰" },
                    { label: "Monthly Projection", value: `₹${result.carbon_forecast.monthly_projection_inr?.toLocaleString("en-IN")}`, icon: "📅" },
                    { label: "Annual Projection",  value: `₹${result.carbon_forecast.annual_projection_inr?.toLocaleString("en-IN")}`, icon: "📈" },
                  ].map(item => (
                    <div key={item.label} className="rounded-lg bg-slate-800/60 border border-slate-700 p-2.5 text-center">
                      <p className="text-lg mb-0.5">{item.icon}</p>
                      <p className="text-xs font-bold text-white">{item.value}</p>
                      <p className="text-[10px] text-slate-400">{item.label}</p>
                    </div>
                  ))}
                </div>
              ) : null}
              <p className="text-[11px] text-slate-400 leading-relaxed"
                dangerouslySetInnerHTML={{ __html: result.carbon_forecast.message.replace(/\*\*(.*?)\*\*/g, "<strong class='text-emerald-300'>$1</strong>") }}
              />
              {result.carbon_forecast.standard && (
                <p className="text-[10px] text-slate-600 mt-2">Standard: {result.carbon_forecast.standard}</p>
              )}
            </div>

            {/* ── No issues ── */}
            {result.alerts.length === 0 && result.recommendations.length === 0 && (
              <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-3">
                <CheckCircle className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <p className="text-xs text-emerald-300">All systems optimal — no risks detected for this dispatch scenario.</p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
