"""LLM Natural Language Understanding (NLU) & Entity Extractor using OpenAI GPT-4o-mini.

Allows users to speak naturally (e.g. "500kg general cargo arriving on 1st oct at Karachi"),
handling flexible date formats, airport city names, weights, and categories intelligently,
while preserving pure deterministic math for tariff calculation.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from zoneinfo import ZoneInfo
from app.config import settings

logger = logging.getLogger("conversation_llm")


SYSTEM_PROMPT = """You are the Natural Language Understanding (NLU) unit for the Gerry’s / dnata Import Cargo Tariff WhatsApp Chatbot in Pakistan.
Your job is to extract structured cargo parameters and user intent from natural language messages.

Current Date in Pakistan: {current_date}

EXTRACTABLE FIELDS:
1. "arrival_date": Date string formatted strictly as "YYYY-MM-DD". In Pakistan, numeric dates follow DD-MM-YYYY or DD/MM/YYYY (e.g. "12-10-2026" is October 12, 2026). Also understand expressions like "today", "yesterday", "tomorrow", "1st Oct", "7-oct-2026", "October 1st 2026", "last Monday", etc. relative to current date.
2. "payment_date": Date string formatted strictly as "YYYY-MM-DD". Follows DD-MM-YYYY format. Payment date is on or after arrival date (e.g. if arrival is 7-Oct-2026, "12-10-2026" means 12-Oct-2026, 5 days dwell). If user says "clearing same day", "today", "tomorrow", "on 5th oct", resolve it.
3. "category": One of ["AFU", "PHARMA", "ICG", "ICG COLD"].
   - "general", "normal cargo", "afu", "freight" -> "AFU"
   - "pharma", "medicine", "pil", "vaccine" -> "PHARMA"
   - "icg", "import cargo general" -> "ICG"
   - "cold", "refrigerated", "freezer", "pharma cold", "icg cold" -> "ICG COLD"
4. "cargo_class": Subclass within category:
   - For AFU: "GEN", "IDT"
   - For PHARMA: "GEN (PIL)"
   - For ICG: "IGEN", "IDT (DR)"
   - For ICG COLD: "2 to 8 Degree Celsius (ICO)", "15 to 25 Degree Celsius (IRT)", "Freezer (IRO)"
   Default to "GEN" or first matching class if standard.
5. "weight_kg": Numeric weight in kilograms (e.g. 500, 1200.5, 80). If user says "2 tons" or "2 tonnes", convert to 2000. If user says "80 kg" or "80", return 80.
6. "station": Airport code: "KHI" (Karachi), "LHE" (Lahore), "ISB" (Islamabad), "MUX" (Multan), "PEW" (Peshawar).
7. "is_oversize": Boolean (true/false) if mentioned (e.g. "heavy pieces", "oversize: yes", "not oversize", "single piece 1200kg").
8. "intent": One of:
   - "reset": User wants to start over, cancel, start a new calculation, or said "new", "start new", "fresh", "start over", "hi", "hello", "salam", "start". Note: only treat "new" as category NEW if explicitly referring to newspapers.
   - "confirm": User agrees/confirms summary ("yes", "confirm", "proceed", "calculate", "ok").
   - "help": User asks for instructions or help.
   - "back": User wants to edit or go back.
   - "info": User provided cargo information or answering a question.

OUTPUT FORMAT:
Return ONLY a valid JSON object with the detected fields.
Only include keys if they are clearly present or implied by the user's message.
Example:
{
  "intent": "info",
  "arrival_date": "2026-10-01",
  "category": "AFU",
  "cargo_class": "GEN",
  "weight_kg": 500,
  "station": "KHI"
}
"""


def extract_with_llm(
    user_text: str,
    current_collected: Optional[Dict[str, Any]] = None,
    current_state: Optional[str] = None,
    last_bot_prompt: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Call GPT-4o-mini to extract parameters with full 5-turn dialogue history."""
    api_key = settings.OPENAI_API_KEY.strip()
    if not api_key:
        return {}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)

        tz = ZoneInfo(settings.APP_TIMEZONE)
        now_str = datetime.now(tz).strftime("%Y-%m-%d (%A)")

        clean_collected = {k: v for k, v in (current_collected or {}).items() if not k.startswith("_")}
        system_msg = SYSTEM_PROMPT.replace("{current_date}", now_str)
        if clean_collected:
            system_msg += f"\n\nAlready confirmed parameters: {json.dumps(clean_collected)}"

        messages = [
            {"role": "system", "content": system_msg},
        ]

        # Add the last 5 turns (up to 10 messages) of conversation history
        if conversation_history:
            for item in conversation_history[-10:]:
                role = item.get("role")
                content = item.get("content")
                if role in ["assistant", "user"] and content:
                    messages.append({"role": role, "content": str(content).strip()})
        elif last_bot_prompt:
            messages.append({"role": "assistant", "content": last_bot_prompt.strip()})

        # Append current user message
        messages.append({"role": "user", "content": user_text.strip()})

        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=250,
            timeout=8.0,
        )

        content = response.choices[0].message.content
        if content:
            data = json.loads(content)
            
            # Post-processing safety: if bot is waiting for payment date and arrival is already set
            if current_state == "AWAITING_PAYMENT_DATE":
                if "arrival_date" in data and "payment_date" not in data:
                    if (current_collected or {}).get("arrival_date"):
                        data["payment_date"] = data.pop("arrival_date")

            logger.info(f"LLM NLU Extracted: {data}")
            return data
    except Exception as e:
        logger.warning(f"LLM extraction skipped or failed: {e}")

    return {}
