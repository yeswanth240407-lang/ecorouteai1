"use client";

import React, { useEffect, useRef } from "react";
import L from "leaflet";

interface MapViewProps {
  depot: { lat: number; lng: number; name: string };
  stops: Array<{ id: string; name: string; lat: number; lng: number; demand: number }>;
  routeGeometry?: Array<[number, number]>;
  baselineGeometry?: Array<[number, number]>;
  selectedRouteName?: string;
}

export default function MapView({
  depot,
  stops,
  routeGeometry = [],
  baselineGeometry = [],
  selectedRouteName
}: MapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const layerGroupRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      // Initialize Leaflet map with India center
      const map = L.map(mapContainerRef.current, {
        center: [depot.lat, depot.lng],
        zoom: 12,
        zoomControl: true,
      });

      // Standard OpenStreetMap tiles (100% free, no watermark, comprehensive road network across India)
      L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
      }).addTo(map);

      const layerGroup = L.layerGroup().addTo(map);
      layerGroupRef.current = layerGroup;
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;
    const layers = layerGroupRef.current;
    if (!map || !layers) return;

    // Clear previous markers & polylines
    layers.clearLayers();

    // 1. Add Depot Marker (Distinct Green Warehouse Badge)
    const depotIcon = L.divIcon({
      className: "custom-depot-icon",
      html: `
        <div style="background: #059669; color: #fff; width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 16px; border: 2.5px solid #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.5);">
          🏢
        </div>
      `,
      iconSize: [36, 36],
      iconAnchor: [18, 18],
    });

    L.marker([depot.lat, depot.lng], { icon: depotIcon })
      .bindPopup(`<div style="color: #0f172a; font-family: sans-serif; font-size: 12px;"><b>CENTRAL DEPOT (INDIA)</b><br/>${depot.name}</div>`)
      .addTo(layers);

    const bounds = L.latLngBounds([[depot.lat, depot.lng]]);

    // 2. Add Stop Markers (Numbered Blue Badges)
    stops.forEach((stop, index) => {
      bounds.extend([stop.lat, stop.lng]);
      const stopIcon = L.divIcon({
        className: "custom-stop-icon",
        html: `
          <div style="background: #2563eb; color: #fff; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 12px; border: 2px solid #ffffff; box-shadow: 0 4px 10px rgba(0,0,0,0.45);">
            ${index + 1}
          </div>
        `,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      L.marker([stop.lat, stop.lng], { icon: stopIcon })
        .bindPopup(`<div style="color: #0f172a; font-family: sans-serif; font-size: 12px;"><b>Stop #${index + 1}: ${stop.name}</b><br/>Demand: <b>${stop.demand} kg</b></div>`)
        .addTo(layers);
    });

    // 3. Render Baseline Route Polyline (dashed gray line)
    if (baselineGeometry && baselineGeometry.length > 1) {
      L.polyline(baselineGeometry, {
        color: "#64748b",
        weight: 3.5,
        dashArray: "7, 9",
        opacity: 0.65,
      }).bindPopup(`<div style="color: #0f172a; font-size: 12px;"><b>Unoptimized Baseline</b></div>`).addTo(layers);
    }

    // 4. Render Active Optimized Route Polyline (vibrant green with outer border)
    if (routeGeometry && routeGeometry.length > 1) {
      // Glow/border underlay
      L.polyline(routeGeometry, {
        color: "#065f46",
        weight: 8,
        opacity: 0.5,
      }).addTo(layers);

      // Core route line
      const activePolyline = L.polyline(routeGeometry, {
        color: "#10b981",
        weight: 5,
        opacity: 0.95,
        lineJoin: "round",
        lineCap: "round",
      }).bindPopup(`<div style="color: #0f172a; font-size: 12px;"><b>${selectedRouteName || "Optimized Green Route"}</b></div>`);
      
      activePolyline.addTo(layers);
      
      routeGeometry.forEach(([lat, lng]) => bounds.extend([lat, lng]));
    }

    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [45, 45], maxZoom: 14 });
    }

    setTimeout(() => {
      map.invalidateSize();
    }, 150);

  }, [depot, stops, routeGeometry, baselineGeometry, selectedRouteName]);

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden shadow-2xl border border-slate-800 bg-slate-900">
      <div ref={mapContainerRef} className="w-full h-full min-h-[480px] z-0" />
      
      {/* Map Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-slate-900/90 backdrop-blur-md px-3.5 py-2.5 rounded-xl border border-slate-700/60 text-xs shadow-xl flex items-center space-x-4">
        <div className="flex items-center space-x-1.5">
          <span className="w-3.5 h-3.5 rounded bg-emerald-600 inline-block border border-white/70 shadow-sm"></span>
          <span className="text-slate-200 font-medium">Depot Hub</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-3 h-3 rounded-full bg-blue-600 inline-block border border-white/70 shadow-sm"></span>
          <span className="text-slate-200 font-medium">Delivery Stop</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-4 h-1.5 bg-emerald-500 inline-block rounded-full shadow-sm"></span>
          <span className="text-emerald-400 font-bold">Eco Route</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className="w-4 h-0.5 border-t-2 border-dashed border-slate-400 inline-block"></span>
          <span className="text-slate-400">Baseline</span>
        </div>
      </div>
    </div>
  );
}
