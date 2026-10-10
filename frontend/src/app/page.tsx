"use client";

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import {
  Leaf,
  Zap,
  DollarSign,
  Compass,
  AlertTriangle,
  Play,
  RotateCcw,
  Sparkles,
  Truck,
  Layers,
  Clock,
  Info,
  MapPin,
  ExternalLink,
  Bot,
  Map as MapIcon,
  Search,
  Check,
  ClipboardList
} from "lucide-react";
import RouteCard from "../components/RouteCard";
import AgentActivityLogs from "../components/AgentActivityLogs";
import EngineInspectorModal from "../components/EngineInspectorModal";
import AIAgentChatPanel from "../components/AIAgentChatPanel";
import EcoRouteAgentPlan from "../components/EcoRouteAgentPlan";

// Dynamically import MapView to disable SSR for Leaflet
const MapView = dynamic(() => import("../components/MapView"), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full min-h-[480px] rounded-2xl bg-slate-900 flex items-center justify-center text-slate-400 font-mono text-sm">
      Loading India Map Tiles...
    </div>
  ),
});

export default function EcoRouteAIDashboard() {
  const [availableCities, setAvailableCities] = useState<any[]>([]);
  const [selectedCity, setSelectedCity] = useState<string>("chennai");
  const [citySearchQuery, setCitySearchQuery] = useState<string>("");
  const [priority, setPriority] = useState<"GREENEST" | "BALANCED" | "FASTEST" | "CHEAPEST">("GREENEST");
  const [weather, setWeather] = useState<string>("clear");
  const [traffic, setTraffic] = useState<number>(1.25);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isDisrupting, setIsDisrupting] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  
  // View Mode: "map", "plan", or "chat"
  const [viewMode, setViewMode] = useState<"map" | "plan" | "chat">("map");

  // Modal Inspector State
  const [inspectorTab, setInspectorTab] = useState<"glec" | "ortools" | "langgraph" | null>(null);

  // Scenario Data
  const [scenario, setScenario] = useState<any>(null);
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);

  // Load cities list and initial scenario
  useEffect(() => {
    fetchCitiesList();
  }, []);

  useEffect(() => {
    loadCityScenario(selectedCity, priority);
  }, [selectedCity]);

  const fetchCitiesList = async () => {
    try {
      const res = await fetch("/api/routes/cities");
      if (res.ok) {
        const data = await res.json();
        setAvailableCities(data);
      }
    } catch (e) {
      console.warn("Could not fetch cities dynamically, using local hubs.");
    }
  };

  const loadCityScenario = async (cityKey: string, currentPriority: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`/api/routes/sample?city=${cityKey}`);
      if (!res.ok) {
        throw new Error(`Failed to load scenario (HTTP ${res.status})`);
      }
      const data = await res.json();
      setScenario(data);
      await executeOptimization(data, currentPriority);
    } catch (err: any) {
      console.error("API error:", err);
      try {
        const directRes = await fetch(`http://127.0.0.1:8000/api/routes/sample?city=${cityKey}`);
        if (directRes.ok) {
          const directData = await directRes.json();
          setScenario(directData);
          await executeOptimization(directData, currentPriority, "http://127.0.0.1:8000");
          setErrorMessage(null);
        }
      } catch (fallbackErr: any) {
        setErrorMessage("Unable to connect to Eco RouteAI backend. Ensure FastAPI server is running on port 8000.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const executeOptimization = async (targetScenario: any, optPriority: string, baseUrl: string = "") => {
    if (!targetScenario) return;
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const payload = {
        ...targetScenario,
        priority: optPriority,
        traffic_congestion_level: traffic,
        weather_condition: weather,
      };

      const url = baseUrl ? `${baseUrl}/api/routes/optimize` : `/api/routes/optimize`;
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorDetail = await res.text();
        throw new Error(`Optimization returned HTTP ${res.status}: ${errorDetail}`);
      }

      const result = await res.json();
      setOptimizationResult(result);
      setSelectedRouteId(result.best_route.route_id);
    } catch (e: any) {
      console.error("Optimization failed:", e);
      setErrorMessage(`Optimization error: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCityChange = (cityId: string) => {
    setSelectedCity(cityId);
  };

  const handlePriorityChange = (p: "GREENEST" | "BALANCED" | "FASTEST" | "CHEAPEST") => {
    setPriority(p);
    if (scenario) {
      executeOptimization(scenario, p);
    }
  };

  const handleSimulateDisruption = async () => {
    if (!scenario) return;
    setIsDisrupting(true);
    try {
      const payload = {
        ...scenario,
        priority,
        traffic_congestion_level: 1.85,
        weather_condition: "rainy",
      };
      setTraffic(1.85);
      setWeather("rainy");

      const res = await fetch(`/api/routes/simulate-disruption`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const result = await res.json();
        setOptimizationResult(result);
        setSelectedRouteId(result.best_route.route_id);
      }
    } catch (e: any) {
      console.error("Disruption simulation failed", e);
    } finally {
      setIsDisrupting(false);
    }
  };

  const handleApplyAgentPlan = (newScenario?: any, newResult?: any, newPriority?: string) => {
    if (newScenario) setScenario(newScenario);
    if (newResult) {
      setOptimizationResult(newResult);
      setSelectedRouteId(newResult.best_route.route_id);
    }
    if (newPriority) {
      setPriority(newPriority as any);
    }
  };

  const filteredCities = (availableCities.length > 0 ? availableCities : [
    { id: "chennai", name: "Chennai (Ponneri Hub)", state: "Tamil Nadu" },
    { id: "bengaluru", name: "Bengaluru", state: "Karnataka" },
    { id: "mumbai", name: "Mumbai MMR", state: "Maharashtra" },
    { id: "delhi", name: "Delhi NCR", state: "National Capital Region" },
    { id: "hyderabad", name: "Hyderabad", state: "Telangana" },
    { id: "pune", name: "Pune", state: "Maharashtra" },
    { id: "kolkata", name: "Kolkata", state: "West Bengal" },
    { id: "ahmedabad", name: "Ahmedabad", state: "Gujarat" },
    { id: "kochi", name: "Kochi", state: "Kerala" },
    { id: "jaipur", name: "Jaipur", state: "Rajasthan" },
    { id: "coimbatore", name: "Coimbatore", state: "Tamil Nadu" },
    { id: "lucknow", name: "Lucknow", state: "Uttar Pradesh" },
    { id: "chandigarh", name: "Chandigarh", state: "Punjab & Haryana" },
    { id: "visakhapatnam", name: "Visakhapatnam", state: "Andhra Pradesh" },
    { id: "indore", name: "Indore", state: "Madhya Pradesh" },
  ]).filter((c) =>
    c.name.toLowerCase().includes(citySearchQuery.toLowerCase()) ||
    c.state.toLowerCase().includes(citySearchQuery.toLowerCase())
  );

  const activeRoute = optimizationResult?.candidate_routes?.find(
    (r: any) => r.route_id === selectedRouteId
  ) || optimizationResult?.best_route;

  const baselineRoute = optimizationResult?.baseline_route;

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
      {/* Top Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/70 backdrop-blur-md sticky top-0 z-40 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-3.5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="font-bold text-lg text-white tracking-tight">Eco RouteAI</h1>
              <span className="text-[11px] bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-medium px-2.5 py-0.5 rounded-full flex items-center space-x-1">
                <span>🇮🇳</span>
                <span>Pan-India Logistics & States Network</span>
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Autonomous Green Dispatch Engine • LangGraph & Google OR-Tools
            </p>
          </div>
        </div>

        {/* Interactive Framework Badges (Clickable Inspectors) */}
        <div className="hidden md:flex items-center space-x-2.5 text-xs">
          <button
            onClick={() => setInspectorTab("glec")}
            title="Click to inspect live GLEC Framework emissions calculations"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-emerald-950/60 border border-slate-700/60 hover:border-emerald-500/60 text-slate-300 hover:text-emerald-300 transition-all cursor-pointer shadow-sm group"
          >
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-medium">GLEC Framework</span>
            <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-emerald-400 transition-colors" />
          </button>

          <button
            onClick={() => setInspectorTab("ortools")}
            title="Click to inspect Google OR-Tools CVRPTW solver variables & constraints"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-blue-950/60 border border-slate-700/60 hover:border-blue-500/60 text-slate-300 hover:text-blue-300 transition-all cursor-pointer shadow-sm group"
          >
            <Layers className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-medium">OR-Tools CVRPTW</span>
            <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-blue-400 transition-colors" />
          </button>

          <button
            onClick={() => setInspectorTab("langgraph")}
            title="Click to inspect LangGraph 5-node agent state machine execution"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-800/80 hover:bg-purple-950/60 border border-slate-700/60 hover:border-purple-500/60 text-slate-300 hover:text-purple-300 transition-all cursor-pointer shadow-sm group"
          >
            <Sparkles className="w-3.5 h-3.5 text-purple-400" />
            <span className="font-medium">LangGraph Multi-Agent</span>
            <ExternalLink className="w-3 h-3 text-slate-500 group-hover:text-purple-400 transition-colors" />
          </button>
        </div>
      </header>

      {/* Error notification banner if any */}
      {errorMessage && (
        <div className="bg-amber-950/60 border-b border-amber-600/40 px-6 py-2.5 text-amber-300 text-xs flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
          <button
            onClick={() => loadCityScenario(selectedCity, priority)}
            className="underline font-semibold hover:text-white"
          >
            Reconnect
          </button>
        </div>
      )}

      {/* Main Grid */}
      <main className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 p-6 max-w-[1600px] w-full mx-auto">
        {/* Left Column: Controls & Decisions (5 cols) */}
        <div className="lg:col-span-5 flex flex-col space-y-5">
          {/* Pan-India Cities & States Hub Selector */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider flex items-center space-x-1.5">
                <MapPin className="w-3.5 h-3.5 text-emerald-400" />
                <span>Indian States & Cities Logistics Hubs</span>
              </label>
              <span className="text-[10px] bg-emerald-500/15 text-emerald-400 font-mono px-2 py-0.5 rounded-full">
                {filteredCities.length} Regions
              </span>
            </div>

            {/* City Search Bar */}
            <div className="relative mb-3">
              <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-3" />
              <input
                type="text"
                value={citySearchQuery}
                onChange={(e) => setCitySearchQuery(e.target.value)}
                placeholder="Search city or state (e.g. Ponneri, Chennai, Pune, Kochi)..."
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-white placeholder-slate-500 focus:border-emerald-500 outline-none"
              />
            </div>
            
            {/* Scrollable Cities Grid */}
            <div className="grid grid-cols-2 gap-2 max-h-44 overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-slate-800">
              {filteredCities.map((c) => (
                <button
                  key={c.id}
                  onClick={() => handleCityChange(c.id)}
                  className={`p-2 rounded-xl text-left border transition-all ${
                    selectedCity === c.id
                      ? "border-emerald-500 bg-emerald-950/30 text-white shadow-md shadow-emerald-950/40 ring-1 ring-emerald-500/50"
                      : "border-slate-800 bg-slate-800/40 text-slate-300 hover:bg-slate-800 hover:text-white"
                  }`}
                >
                  <div className="font-semibold text-xs text-slate-100 truncate">{c.name}</div>
                  <div className="text-[10px] text-slate-400 truncate">{c.state}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Priority Tabs */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-xl">
            <label className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2.5">
              Optimization Objective
            </label>
            <div className="grid grid-cols-4 gap-2">
              <button
                onClick={() => handlePriorityChange("GREENEST")}
                className={`flex flex-col items-center justify-center py-2.5 px-2 rounded-xl text-xs font-medium transition-all ${
                  priority === "GREENEST"
                    ? "bg-emerald-600 text-white shadow-lg shadow-emerald-600/30 ring-2 ring-emerald-400"
                    : "bg-slate-800/60 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Leaf className="w-4 h-4 mb-1" />
                Greenest
              </button>

              <button
                onClick={() => handlePriorityChange("BALANCED")}
                className={`flex flex-col items-center justify-center py-2.5 px-2 rounded-xl text-xs font-medium transition-all ${
                  priority === "BALANCED"
                    ? "bg-teal-600 text-white shadow-lg shadow-teal-600/30 ring-2 ring-teal-400"
                    : "bg-slate-800/60 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Compass className="w-4 h-4 mb-1" />
                Balanced
              </button>

              <button
                onClick={() => handlePriorityChange("FASTEST")}
                className={`flex flex-col items-center justify-center py-2.5 px-2 rounded-xl text-xs font-medium transition-all ${
                  priority === "FASTEST"
                    ? "bg-sky-600 text-white shadow-lg shadow-sky-600/30 ring-2 ring-sky-400"
                    : "bg-slate-800/60 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <Zap className="w-4 h-4 mb-1" />
                Fastest
              </button>

              <button
                onClick={() => handlePriorityChange("CHEAPEST")}
                className={`flex flex-col items-center justify-center py-2.5 px-2 rounded-xl text-xs font-medium transition-all ${
                  priority === "CHEAPEST"
                    ? "bg-amber-600 text-white shadow-lg shadow-amber-600/30 ring-2 ring-amber-400"
                    : "bg-slate-800/60 text-slate-300 hover:bg-slate-800 hover:text-white"
                }`}
              >
                <DollarSign className="w-4 h-4 mb-1" />
                Cheapest
              </button>
            </div>

            {/* Quick Action Buttons */}
            <div className="flex items-center space-x-3 mt-4 pt-3 border-t border-slate-800/80">
              <button
                onClick={() => executeOptimization(scenario, priority)}
                disabled={isLoading}
                className="flex-1 flex items-center justify-center space-x-2 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs rounded-xl shadow-lg shadow-emerald-500/20 transition-all disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{isLoading ? "Agents Solving..." : "Re-Optimize Route"}</span>
              </button>

              <button
                onClick={handleSimulateDisruption}
                disabled={isDisrupting || isLoading}
                className="flex items-center space-x-2 py-2.5 px-3 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/30 font-medium text-xs rounded-xl transition-all disabled:opacity-50"
                title="Simulates monsoon rain & peak Indian road traffic to trigger dynamic re-routing"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>Simulate Jam</span>
              </button>
            </div>
          </div>

          {/* Environmental Savings Summary */}
          {optimizationResult && (
            <div className="bg-gradient-to-br from-emerald-950/40 via-slate-900 to-slate-900 border border-emerald-500/30 rounded-2xl p-4 shadow-xl">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider flex items-center space-x-1.5">
                  <Leaf className="w-4 h-4 text-emerald-400" />
                  <span>Verified Ecological Impact</span>
                </span>
                <button
                  onClick={() => setInspectorTab("glec")}
                  className="text-[10px] bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded-full font-mono flex items-center space-x-1 cursor-pointer transition-colors"
                >
                  <span>GLEC Verified</span>
                  <ExternalLink className="w-2.5 h-2.5" />
                </button>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">CO₂ Slashed</span>
                  <div className="text-2xl font-bold text-emerald-400 mt-0.5">
                    {optimizationResult.co2_saved_pct}%
                  </div>
                  <span className="text-[10px] text-emerald-500 font-medium">
                    -{optimizationResult.co2_saved_kg} kg CO₂
                  </span>
                </div>

                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Time Delta</span>
                  <div className="text-2xl font-bold text-sky-400 mt-0.5">
                    {activeRoute && baselineRoute
                      ? (activeRoute.total_time_min - baselineRoute.total_time_min).toFixed(1)
                      : "0"}m
                  </div>
                  <span className="text-[10px] text-slate-400">vs unoptimized</span>
                </div>

                <div className="bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block">Cost Variance</span>
                  <div className="text-2xl font-bold text-teal-400 mt-0.5">
                    ${optimizationResult.cost_saved > 0 ? `-${optimizationResult.cost_saved}` : `+${Math.abs(optimizationResult.cost_saved)}`}
                  </div>
                  <span className="text-[10px] text-slate-400">fuel & labor</span>
                </div>
              </div>

              {/* Explainer Agent Output */}
              <div className="mt-3.5 p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-300 leading-relaxed flex items-start space-x-2.5">
                <Info className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <strong className="text-emerald-400 font-semibold block mb-0.5">
                    Explainer Agent Verdict:
                  </strong>
                  {optimizationResult.explanation}
                </div>
              </div>
            </div>
          )}

          {/* Candidate Routes List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                Evaluated Fleet Candidates
              </h3>
              <span className="text-xs text-slate-500">
                {optimizationResult?.candidate_routes?.length || 0} evaluated
              </span>
            </div>

            <div className="space-y-2.5">
              {optimizationResult?.candidate_routes?.map((route: any) => (
                <RouteCard
                  key={route.route_id}
                  route={route}
                  isSelected={route.route_id === (selectedRouteId || optimizationResult.best_route.route_id)}
                  onSelect={() => setSelectedRouteId(route.route_id)}
                  isBaseline={route.tag === "Baseline (Unoptimized)"}
                />
              ))}
            </div>
          </div>

          {/* LangGraph Agent Activity Logs */}
          {optimizationResult?.agent_logs && (
            <AgentActivityLogs logs={optimizationResult.agent_logs} />
          )}
        </div>

        {/* Right Column: View Switcher (Live Map VS AI Agent Copilot) (7 cols) */}
        <div className="lg:col-span-7 flex flex-col space-y-4">
          {/* View Mode Switcher Header */}
          <div className="flex items-center justify-between bg-slate-900 border border-slate-800 p-2 rounded-2xl shadow-lg">
            <div className="flex items-center space-x-1.5 sm:space-x-2">
              <button
                onClick={() => setViewMode("map")}
                className={`flex items-center space-x-1.5 sm:space-x-2 px-3 sm:px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  viewMode === "map"
                    ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                <MapIcon className="w-4 h-4" />
                <span>Interactive Route Map</span>
              </button>

              <button
                onClick={() => setViewMode("plan")}
                className={`flex items-center space-x-1.5 sm:space-x-2 px-3 sm:px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  viewMode === "plan"
                    ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                <ClipboardList className="w-4 h-4 text-emerald-400" />
                <span>Eco Route Agent Plan</span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              </button>

              <button
                onClick={() => setViewMode("chat")}
                className={`flex items-center space-x-1.5 sm:space-x-2 px-3 sm:px-4 py-2 rounded-xl text-xs font-semibold transition-all ${
                  viewMode === "chat"
                    ? "bg-emerald-600 text-white shadow-md shadow-emerald-600/30"
                    : "text-slate-400 hover:text-white hover:bg-slate-800"
                }`}
              >
                <Bot className="w-4 h-4 text-emerald-300" />
                <span>AI Agent Copilot</span>
              </button>
            </div>

            <div className="text-xs text-slate-500 pr-3 hidden md:block font-mono">
              {viewMode === "map" && "Visual Road Coordinates"}
              {viewMode === "plan" && "LangGraph + OR-Tools + GLEC"}
              {viewMode === "chat" && "Natural Language Re-Planner"}
            </div>
          </div>

          {/* View Container */}
          {viewMode === "map" && (
            <div className="flex flex-col space-y-5 animate-in fade-in duration-200">
              {/* Leaflet Map Box */}
              <div className="h-[500px] w-full">
                {scenario ? (
                  <MapView
                    depot={scenario.depot}
                    stops={scenario.stops}
                    routeGeometry={activeRoute?.geometry || []}
                    baselineGeometry={baselineRoute?.geometry || []}
                    selectedRouteName={activeRoute?.title}
                  />
                ) : (
                  <div className="w-full h-full rounded-2xl bg-slate-900 flex items-center justify-center text-slate-400">
                    Loading Indian Logistics Network...
                  </div>
                )}
              </div>

              {/* Itinerary & Stop Sequence */}
              {activeRoute && (
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-semibold text-slate-100 text-sm flex items-center space-x-2">
                        <Truck className="w-4 h-4 text-emerald-400" />
                        <span>Indian Delivery Dispatch Sequence</span>
                      </h3>
                      <p className="text-xs text-slate-400 mt-0.5">
                        Vehicle: <strong className="text-slate-200">{activeRoute.vehicle_name}</strong> ({activeRoute.vehicle_type})
                      </p>
                    </div>
                    <div className="text-xs text-slate-400 text-right">
                      <div>Stops Count: <strong className="text-slate-200">{activeRoute.steps.length - 2}</strong></div>
                      <div>Total Distance: <strong className="text-slate-200">{activeRoute.total_distance_km} km</strong></div>
                    </div>
                  </div>

                  <div className="divide-y divide-slate-800/80 max-h-56 overflow-y-auto pr-2">
                    {activeRoute.steps.map((step: any, index: number) => {
                      const isDepot = index === 0 || index === activeRoute.steps.length - 1;
                      return (
                        <div key={index} className="py-2.5 flex items-center justify-between text-xs">
                          <div className="flex items-center space-x-3">
                            <span
                              className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold ${
                                isDepot
                                  ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                                  : "bg-blue-500/20 text-blue-400 border border-blue-500/40"
                              }`}
                            >
                              {isDepot ? "D" : index}
                            </span>
                            <div>
                              <div className="font-medium text-slate-200">{step.name}</div>
                              <div className="text-[11px] text-slate-400 flex items-center space-x-2">
                                <span>+{step.distance_from_prev_km} km</span>
                                <span>•</span>
                                <span>{step.time_from_prev_min} min transit</span>
                              </div>
                            </div>
                          </div>

                          <div className="text-right">
                            <div className="font-mono text-slate-200">
                              {step.arrival_time_min} min
                            </div>
                            <div className="text-[10px] text-slate-500 font-mono">
                              {step.step_co2_kg} kg CO₂
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          )}

          {viewMode === "plan" && (
            <div className="animate-in fade-in duration-200">
              <EcoRouteAgentPlan
                scenario={scenario}
                optimizationResult={optimizationResult}
                isLoading={isLoading}
                priority={priority}
                onExecutePlan={() => executeOptimization(scenario, priority)}
                onOpenInspector={(tab) => setInspectorTab(tab)}
                onPriorityChange={handlePriorityChange}
                onSimulateDisruption={handleSimulateDisruption}
              />
            </div>
          )}

          {viewMode === "chat" && (
            <div className="animate-in fade-in duration-200">
              <AIAgentChatPanel
                scenario={scenario}
                currentPriority={priority}
                trafficLevel={traffic}
                weather={weather}
                onApplyNewPlan={handleApplyAgentPlan}
              />
            </div>
          )}
        </div>
      </main>

      {/* Interactive Modal Inspector for GLEC, OR-Tools, and LangGraph */}
      <EngineInspectorModal
        activeTab={inspectorTab}
        onClose={() => setInspectorTab(null)}
        optimizationResult={optimizationResult}
        scenario={scenario}
        onRunVerification={() => executeOptimization(scenario, priority)}
      />
    </div>
  );
}
