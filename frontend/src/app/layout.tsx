import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Eco RouteAI - Multi-Agent Green Logistics",
  description: "Autonomous route optimization balancing CO2, cost, and time using LangGraph & OR-Tools",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased selection:bg-emerald-500 selection:text-white">
        {children}
      </body>
    </html>
  );
}
