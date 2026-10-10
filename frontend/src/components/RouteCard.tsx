"use client";

import React from "react";
import { Leaf, Clock, DollarSign, Route as RouteIcon, CheckCircle2 } from "lucide-react";

interface RouteCardProps {
  route: {
    route_id: string;
    title: string;
    vehicle_name: string;
    vehicle_type: string;
    total_distance_km: number;
    total_time_min: number;
    total_co2_kg: number;
    total_cost: number;
    tag?: string;
  };
  isSelected: boolean;
  onSelect: () => void;
  isBaseline?: boolean;
}

export default function RouteCard({
  route,
  isSelected,
  onSelect,
  isBaseline = false,
}: RouteCardProps) {
  const isGreenest = route.tag === "Greenest Choice";

  return (
    <div
      onClick={onSelect}
      className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 ${
        isSelected
          ? isGreenest
            ? "border-emerald-500 bg-emerald-950/20 shadow-lg shadow-emerald-950/50"
            : "border-blue-500 bg-blue-950/20 shadow-lg shadow-blue-950/50"
          : "border-slate-800 bg-slate-900/60 hover:border-slate-700 hover:bg-slate-900"
      }`}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="flex items-center space-x-2">
            <span
              className={`text-xs px-2 py-0.5 rounded-full font-semibold ${
                isGreenest
                  ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                  : isBaseline
                  ? "bg-slate-700/50 text-slate-300 border border-slate-600/40"
                  : "bg-blue-500/20 text-blue-300 border border-blue-500/30"
              }`}
            >
              {route.tag || "Alternative Route"}
            </span>
            <span className="text-xs text-slate-400">{route.vehicle_type}</span>
          </div>
          <h4 className="font-semibold text-slate-100 text-sm mt-1">{route.vehicle_name}</h4>
        </div>
        {isSelected && (
          <CheckCircle2
            className={`w-5 h-5 ${isGreenest ? "text-emerald-400" : "text-blue-400"}`}
          />
        )}
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs mt-3">
        <div className="flex items-center space-x-1.5 text-slate-300 bg-slate-800/40 px-2 py-1.5 rounded-lg">
          <Leaf className={`w-3.5 h-3.5 ${isGreenest ? "text-emerald-400" : "text-amber-400"}`} />
          <span>
            <strong className="text-slate-100">{route.total_co2_kg}</strong> kg CO₂
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-300 bg-slate-800/40 px-2 py-1.5 rounded-lg">
          <Clock className="w-3.5 h-3.5 text-sky-400" />
          <span>
            <strong className="text-slate-100">{route.total_time_min}</strong> min
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-300 bg-slate-800/40 px-2 py-1.5 rounded-lg">
          <DollarSign className="w-3.5 h-3.5 text-emerald-400" />
          <span>
            <strong className="text-slate-100">${route.total_cost}</strong> est.
          </span>
        </div>

        <div className="flex items-center space-x-1.5 text-slate-300 bg-slate-800/40 px-2 py-1.5 rounded-lg">
          <RouteIcon className="w-3.5 h-3.5 text-purple-400" />
          <span>
            <strong className="text-slate-100">{route.total_distance_km}</strong> km
          </span>
        </div>
      </div>
    </div>
  );
}
