import os
import httpx
from typing import Optional, Dict, Any

class GeminiService:
    """
    Service wrapper for Google Gemini API.
    Provides intelligent reasoning for EcoRoute AI:
    - Interpreting natural language dispatch instructions
    - Explaining GLEC emissions & route trade-offs
    - Dynamic risk and sustainability advisories
    """

    # Model fallback chain — try each in order until one succeeds
    MODEL_FALLBACK_CHAIN = [
        "gemini-3.5-flash-lite",   # ✅ confirmed working
        "gemini-3.8-flash",
        "gemini-flash-latest",
    ]

    @classmethod
    def get_api_key(cls) -> Optional[str]:
        return os.getenv("GEMINI_API_KEY")

    @classmethod
    async def generate_response(
        cls,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.3
    ) -> Optional[str]:
        api_key = cls.get_api_key()
        if not api_key:
            return None

        payload: Dict[str, Any] = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 450
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        # Try each model in the fallback chain
        for model in cls.MODEL_FALLBACK_CHAIN:
            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:generateContent?key={api_key}"
            )
            try:
                async with httpx.AsyncClient(timeout=12.0) as client:
                    res = await client.post(url, json=payload)
                    if res.status_code == 200:
                        data = res.json()
                        candidates = data.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            if parts:
                                text = parts[0].get("text", "").strip()
                                if text:
                                    print(f"[GeminiService] Success with model: {model}")
                                    return text
                    elif res.status_code in (404, 410):
                        # Model not found — try next
                        print(f"[GeminiService] Model {model} not found (404/410), trying next...")
                        continue
                    elif res.status_code == 503:
                        # High demand — try next model
                        print(f"[GeminiService] Model {model} overloaded (503), trying next...")
                        continue
                    else:
                        err = res.json().get("error", {}).get("message", "unknown")
                        print(f"[GeminiService] Model {model} HTTP {res.status_code}: {err[:100]}")
                        continue
            except httpx.TimeoutException:
                print(f"[GeminiService] Model {model} timed out, trying next...")
                continue
            except Exception as e:
                print(f"[GeminiService] Model {model} error: {type(e).__name__}: {e}")
                continue

        print("[GeminiService] All models exhausted — returning None")
        return None

    @classmethod
    async def answer_general_query(cls, user_message: str, current_depot: str, current_stops: int) -> Optional[str]:
        system_prompt = (
            "You are the Gemini AI Copilot for EcoRoute AI, an autonomous Indian green logistics and EV fleet optimization platform. "
            "You help logistics dispatchers optimize deliveries across 30+ Indian hubs (Chennai, Bengaluru, Delhi, Mumbai, Madurai, etc.). "
            "Respond helpfully and concisely (under 80 words) using Markdown, emojis (🌿, ⚡, 📍, 🚛), and clear bullet points. "
            "Mention how they can use commands like 'Switch to Madurai', 'Add delivery to Indiranagar (50 kg)', or 'Optimize for greenest emissions'."
        )
        prompt = (
            f"Current dispatch context: Depot = {current_depot}, Stops = {current_stops}.\n"
            f"User asks: {user_message}"
        )
        return await cls.generate_response(prompt, system_instruction=system_prompt)

    @classmethod
    async def generate_dispatch_brief(
        cls,
        user_message: str,
        action_taken: str,
        depot_name: str,
        stops_count: int,
        best_vehicle: str,
        co2_reduction_pct: float,
        co2_saved_kg: float,
        priority: str
    ) -> Optional[str]:
        system_prompt = (
            "You are the Gemini AI Copilot for EcoRoute AI. "
            "Generate a crisp, professional 2-3 sentence dispatch summary emphasizing EV emissions savings and route efficiency. "
            "Include key stats (CO2 saved, vehicle selected). Format with Markdown."
        )
        prompt = (
            f"User request: '{user_message}'\n"
            f"Action: {action_taken}\n"
            f"Depot: {depot_name}\n"
            f"Stops count: {stops_count}\n"
            f"Selected fleet vehicle: {best_vehicle}\n"
            f"Priority: {priority}\n"
            f"CO2 reduction: {co2_reduction_pct}% ({co2_saved_kg} kg CO2 saved vs diesel baseline)\n"
            f"Generate a concise autonomous dispatch brief."
        )
        return await cls.generate_response(prompt, system_instruction=system_prompt)

    @classmethod
    async def generate_advisory_insights(
        cls,
        depot_name: str,
        stops_count: int,
        weather: str,
        traffic: float,
        risk_score: int
    ) -> Optional[str]:
        system_prompt = (
            "You are the Predictive Risk & Advisory Agent in EcoRoute AI powered by Google Gemini. "
            "Generate a sharp, 2-sentence proactive advisory tip for Indian delivery fleet dispatchers. "
            "Focus on weather, traffic bottlenecks, and battery range/charging efficiency. Keep under 50 words."
        )
        prompt = (
            f"Corridor: {depot_name} with {stops_count} delivery stops.\n"
            f"Weather condition: {weather}\n"
            f"Traffic multiplier: {traffic}x\n"
            f"Calculated risk index: {risk_score}/100\n"
            f"Provide an actionable predictive risk insight."
        )
        return await cls.generate_response(prompt, system_instruction=system_prompt)
