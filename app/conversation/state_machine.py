"""Persistent WhatsApp conversation state machine."""

from datetime import datetime, timezone, timedelta, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from app.config import settings
from app.db.models import ChatSession, CalculationRecord, OutboxJob
from app.domain.models import CalculationInput, TariffProfile
from app.domain.calculator import calculate_tariff
from app.domain.catalog import CATEGORY_CLASS_MAP
from app.conversation.parser import (
    parse_date_input,
    parse_weight_input,
    parse_category_input,
    parse_cargo_class_input,
    parse_station_input,
    parse_oversize_input,
)
import re
from app.conversation.llm import extract_with_llm
from app.conversation.messages import (
    WELCOME_MESSAGE,
    PROMPT_ARRIVAL_DATE,
    PROMPT_PAYMENT_DATE,
    PROMPT_CATEGORY,
    PROMPT_WEIGHT,
    PROMPT_STATION,
    PROMPT_OVERSIZE,
    HELP_MESSAGE,
    SESSION_EXPIRED_NOTIFICATION,
    format_cargo_class_prompt,
    format_review_summary,
    format_calculation_result,
)


class ConversationEngine:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_session(self, session_id: str) -> Tuple[ChatSession, bool]:
        """Fetch or initialize session with TTL check."""
        now = datetime.now(timezone.utc)
        ttl = timedelta(minutes=settings.SESSION_TTL_MINUTES)
        session = self.db.query(ChatSession).filter_by(session_id=session_id).first()

        is_expired = False
        if session:
            # Check expiration
            # Handle naive datetime from sqlite if any
            exp = session.expires_at
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if now > exp:
                is_expired = True
                session.current_state = "START"
                session.collected_data = {}
                session.last_active_at = now
                session.expires_at = now + ttl
                self.db.commit()
            else:
                session.last_active_at = now
                session.expires_at = now + ttl
                self.db.commit()
        else:
            session = ChatSession(
                session_id=session_id,
                current_state="START",
                collected_data={},
                last_active_at=now,
                created_at=now,
                expires_at=now + ttl,
                version=1,
            )
            self.db.add(session)
            self.db.commit()
            self.db.refresh(session)

        return session, is_expired

    def _finalize(self, session: ChatSession, user_text: str, reply_text: str, prefix: str = "") -> str:
        """Store turn in rolling history (last 5 questions and 5 answers = 10 messages) and commit."""
        data = dict(session.collected_data or {})
        history = list(data.get("_history") or [])
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": reply_text})
        data["_history"] = history[-10:]
        session.collected_data = data
        self.db.commit()
        return prefix + reply_text

    def process_message(self, session_id: str, raw_text: str) -> str:
        """Process an inbound user message and return the response text."""
        session, is_expired = self.get_or_create_session(session_id)
        text = raw_text.strip()
        cmd = text.lower()

        prefix = SESSION_EXPIRED_NOTIFICATION if is_expired else ""

        # Global commands & fresh session triggers
        clean_cmd = re.sub(r"[^\w\s]", "", cmd).strip()
        if clean_cmd in [
            "new", "new calculation", "start new", "fresh", "start fresh", "new session",
            "restart", "cancel", "reset", "clear", "start over",
            "hi", "hello", "hey", "salam", "start", "menu"
        ]:
            session.current_state = "AWAITING_ARRIVAL_DATE"
            session.collected_data = {
                "_history": [{"role": "assistant", "content": WELCOME_MESSAGE}]
            }
            self.db.commit()
            return prefix + WELCOME_MESSAGE

        if cmd == "help":
            help_resp = HELP_MESSAGE + "\n\n" + self._prompt_for_state(session)
            return self._finalize(session, text, help_resp, prefix)

        if cmd == "back":
            prev_msg = self._handle_back(session)
            return self._finalize(session, text, prev_msg, prefix)

        # Step 1: Try deterministic parsing first (for direct options like '2', 'AFU', 'yes', 'no', '1000', 'KHI')
        saved_state = session.current_state
        saved_data = dict(session.collected_data or {})

        direct_response = self._step(session, text)
        if not direct_response.startswith("Error:"):
            # Direct parser succeeded with 100% precision
            return self._finalize(session, text, direct_response, prefix)

        # If direct parser recognized the input but rejected on date ordering, return it directly
        if "cannot be earlier than arrival date" in direct_response:
            return self._finalize(session, text, direct_response, prefix)

        # Revert session state before LLM fallback attempt
        session.current_state = saved_state
        session.collected_data = saved_data

        # Step 2: Fallback to LLM Natural Language Understanding (with last 5 questions and answers)
        if settings.OPENAI_API_KEY.strip():
            last_bot_prompt = self._prompt_for_state(session)
            history = list((session.collected_data or {}).get("_history") or [])
            llm_data = extract_with_llm(
                raw_text,
                session.collected_data,
                session.current_state,
                last_bot_prompt=last_bot_prompt,
                conversation_history=history,
            )
            intent = llm_data.get("intent")

            if intent == "reset":
                session.current_state = "AWAITING_ARRIVAL_DATE"
                session.collected_data = {
                    "_history": [{"role": "assistant", "content": WELCOME_MESSAGE}]
                }
                self.db.commit()
                return prefix + WELCOME_MESSAGE

            if intent == "help":
                help_resp = HELP_MESSAGE + "\n\n" + self._prompt_for_state(session)
                return self._finalize(session, text, help_resp, prefix)

            if intent == "back":
                prev_msg = self._handle_back(session)
                return self._finalize(session, text, prev_msg, prefix)

            if intent == "confirm" and session.current_state == "REVIEW":
                response = self._step(session, "yes")
                return self._finalize(session, text, response, prefix)

            # Check if any cargo fields were extracted
            extracted_any = False
            data = dict(session.collected_data or {})

            if "arrival_date" in llm_data and llm_data["arrival_date"]:
                data["arrival_date"] = str(llm_data["arrival_date"])
                extracted_any = True

            if "payment_date" in llm_data and llm_data["payment_date"]:
                data["payment_date"] = str(llm_data["payment_date"])
                extracted_any = True

            # Validate date ordering
            if data.get("arrival_date") and data.get("payment_date"):
                if data["payment_date"] < data["arrival_date"]:
                    data.pop("payment_date", None)
                    session.collected_data = data
                    date_err = f"Error: Payment date cannot be earlier than arrival date ({data['arrival_date']}).\n\n{PROMPT_PAYMENT_DATE}"
                    return self._finalize(session, text, date_err, prefix)

            if "category" in llm_data and llm_data["category"] in CATEGORY_CLASS_MAP:
                data["category"] = str(llm_data["category"])
                extracted_any = True

            if "cargo_class" in llm_data and llm_data["cargo_class"]:
                cat = data.get("category", "AFU")
                allowed_classes = CATEGORY_CLASS_MAP.get(cat, [])
                cls_candidate = str(llm_data["cargo_class"]).upper()
                if cls_candidate in allowed_classes:
                    data["cargo_class"] = cls_candidate
                    extracted_any = True
                elif "GEN" in allowed_classes:
                    data["cargo_class"] = "GEN"
                    extracted_any = True

            if "weight_kg" in llm_data and llm_data["weight_kg"]:
                try:
                    w = Decimal(str(llm_data["weight_kg"]))
                    if w > 0:
                        data["weight_kg"] = str(w)
                        extracted_any = True
                except Exception:
                    pass

            if "station" in llm_data and llm_data["station"] in ["KHI", "LHE", "ISB", "PEW"]:
                data["station"] = str(llm_data["station"])
                extracted_any = True

            if "is_oversize" in llm_data and isinstance(llm_data["is_oversize"], bool):
                data["is_oversize"] = llm_data["is_oversize"]
                extracted_any = True

            if extracted_any:
                session.collected_data = data
                # Determine next state
                required_fields = [
                    ("arrival_date", "AWAITING_ARRIVAL_DATE"),
                    ("payment_date", "AWAITING_PAYMENT_DATE"),
                    ("category", "AWAITING_CATEGORY"),
                    ("cargo_class", "AWAITING_CARGO_CLASS"),
                    ("weight_kg", "AWAITING_WEIGHT"),
                    ("station", "AWAITING_STATION"),
                    ("is_oversize", "AWAITING_OVERSIZE"),
                ]

                # If category is set but class is missing, default class to GEN if available
                if "category" in data and "cargo_class" not in data:
                    allowed = CATEGORY_CLASS_MAP.get(data["category"], [])
                    if "GEN" in allowed:
                        data["cargo_class"] = "GEN"

                next_state = None
                for field, target_state in required_fields:
                    if field not in data:
                        next_state = target_state
                        break

                if not next_state:
                    session.current_state = "REVIEW"
                    review_msg = format_review_summary(data)
                    return self._finalize(session, text, review_msg, prefix)
                else:
                    session.current_state = next_state
                    prompt_msg = self._prompt_for_state(session)
                    return self._finalize(session, text, prompt_msg, prefix)

        # If LLM didn't resolve or wasn't configured, return the direct parsing guidance error
        return self._finalize(session, text, direct_response, prefix)

    def _step(self, session: ChatSession, text: str) -> str:
        state = session.current_state
        data = dict(session.collected_data or {})

        if state == "START":
            session.current_state = "AWAITING_ARRIVAL_DATE"
            return WELCOME_MESSAGE

        elif state == "AWAITING_ARRIVAL_DATE":
            dt, err = parse_date_input(text)
            if err:
                return f"Error: {err}\n\n{PROMPT_ARRIVAL_DATE}"
            data["arrival_date"] = dt.isoformat()
            session.collected_data = data

            if data.get("editing_from_review"):
                data.pop("editing_from_review", None)
                # Re-validate arrival <= payment if payment already set
                if data.get("payment_date") and data["payment_date"] < data["arrival_date"]:
                    session.current_state = "AWAITING_PAYMENT_DATE"
                    return (
                        f"Notice: Arrival date updated to `{data['arrival_date']}`.\n"
                        f"Payment date `{data['payment_date']}` is now earlier than arrival date.\n\n"
                        f"{PROMPT_PAYMENT_DATE}"
                    )
                session.current_state = "REVIEW"
                return "Arrival date updated.\n\n" + format_review_summary(data)

            session.current_state = "AWAITING_PAYMENT_DATE"
            return f"Arrival Date: `{dt.isoformat()}`\n\n{PROMPT_PAYMENT_DATE}"

        elif state == "AWAITING_PAYMENT_DATE":
            dt, err = parse_date_input(text)
            if err:
                return f"Error: {err}\n\n{PROMPT_PAYMENT_DATE}"

            arr_str = data.get("arrival_date")
            arr_date = date.fromisoformat(arr_str) if arr_str else dt
            if dt < arr_date:
                return (
                    f"Error: Payment date ({dt.isoformat()}) cannot be earlier than arrival date ({arr_date.isoformat()}).\n\n"
                    f"{PROMPT_PAYMENT_DATE}"
                )

            data["payment_date"] = dt.isoformat()
            session.collected_data = data

            if data.get("editing_from_review"):
                data.pop("editing_from_review", None)
                session.current_state = "REVIEW"
                return "Payment date updated.\n\n" + format_review_summary(data)

            session.current_state = "AWAITING_CATEGORY"
            return f"Payment Date: `{dt.isoformat()}`\n\n{PROMPT_CATEGORY}"

        elif state == "AWAITING_CATEGORY":
            cat, err = parse_category_input(text)
            if err:
                return f"Error: {err}\n\n{PROMPT_CATEGORY}"

            prev_cat = data.get("category")
            data["category"] = cat

            # If category changed, cargo class might be invalid
            if prev_cat != cat:
                data.pop("cargo_class", None)

            session.collected_data = data
            classes = CATEGORY_CLASS_MAP[cat]

            # If editing and previously chosen class is still compatible
            if data.get("editing_from_review") and data.get("cargo_class") in classes:
                data.pop("editing_from_review", None)
                session.current_state = "REVIEW"
                return f"Category updated to *{cat}*.\n\n" + format_review_summary(data)

            session.current_state = "AWAITING_CARGO_CLASS"
            return f"Category: *{cat}*\n\n" + format_cargo_class_prompt(cat, classes)

        elif state == "AWAITING_CARGO_CLASS":
            cat = data.get("category", "AFU")
            c_class, err = parse_cargo_class_input(text, cat)
            if err:
                classes = CATEGORY_CLASS_MAP.get(cat, [])
                return f"Error: {err}\n\n" + format_cargo_class_prompt(cat, classes)

            data["cargo_class"] = c_class
            session.collected_data = data

            if data.get("editing_from_review"):
                data.pop("editing_from_review", None)
                session.current_state = "REVIEW"
                return f"Cargo class updated to *{c_class}*.\n\n" + format_review_summary(data)

            session.current_state = "AWAITING_WEIGHT"
            return f"Cargo Class: *{c_class}*\n\n{PROMPT_WEIGHT}"

        elif state == "AWAITING_WEIGHT":
            wt, err = parse_weight_input(text)
            if err:
                return f"Error: {err}\n\n{PROMPT_WEIGHT}"

            data["weight_kg"] = str(wt)
            session.collected_data = data

            if data.get("editing_from_review"):
                data.pop("editing_from_review", None)
                session.current_state = "REVIEW"
                return f"Weight updated to *{wt} kg*.\n\n" + format_review_summary(data)

            session.current_state = "AWAITING_STATION"
            return f"Weight: *{wt} kg*\n\n{PROMPT_STATION}"

        elif state == "AWAITING_STATION":
            st, err = parse_station_input(text)
            if err:
                return f"Error: {err}\n\n{PROMPT_STATION}"

            data["station"] = st
            session.collected_data = data

            if data.get("editing_from_review"):
                data.pop("editing_from_review", None)
                session.current_state = "REVIEW"
                return f"Station updated to *{st}*.\n\n" + format_review_summary(data)

            session.current_state = "AWAITING_OVERSIZE"
            return f"Station: *{st}*\n\n{PROMPT_OVERSIZE}"

        elif state == "AWAITING_OVERSIZE":
            ov, err = parse_oversize_input(text)
            if err:
                return f"Error: {err}\n\n{PROMPT_OVERSIZE}"

            data["is_oversize"] = ov
            data.pop("editing_from_review", None)
            session.collected_data = data
            session.current_state = "REVIEW"
            return format_review_summary(data)

        elif state == "REVIEW":
            cmd = text.strip().lower()
            if cmd in ["confirm", "calculate", "ok", "yes", "1"]:
                return self._execute_calculation(session)

            # Check for field edit request
            edit_step = self._check_edit_request(cmd)
            if edit_step:
                session.current_state = edit_step
                data["editing_from_review"] = True
                session.collected_data = data
                return self._prompt_for_state(session)

            return (
                "Error: Unrecognized command.\n\n"
                "• Reply *CONFIRM* to calculate tariff.\n"
                "• Or reply with a field number (1-7) to edit that value."
            )

        elif state == "RESULT":
            # Any input in result state begins a new calculation
            session.current_state = "AWAITING_ARRIVAL_DATE"
            session.collected_data = {}
            return WELCOME_MESSAGE

        # Fallback
        session.current_state = "AWAITING_ARRIVAL_DATE"
        return WELCOME_MESSAGE

    def _execute_calculation(self, session: ChatSession) -> str:
        data = dict(session.collected_data or {})
        try:
            inp = CalculationInput(
                arrival_date=date.fromisoformat(data["arrival_date"]),
                payment_date=date.fromisoformat(data["payment_date"]),
                category=data["category"],
                cargo_class=data["cargo_class"],
                weight_kg=Decimal(data["weight_kg"]),
                station=data["station"],
                is_oversize=bool(data.get("is_oversize", False)),
            )
        except Exception as e:
            session.current_state = "REVIEW"
            return f"Error: Validating shipment parameters: {str(e)}\n\n" + format_review_summary(data)

        profile = settings.TARIFF_PROFILE
        res = calculate_tariff(inp, profile=profile)

        # Persist calculation record
        calc_record = CalculationRecord(
            calculation_id=res.calculation_id,
            session_id=session.session_id,
            inputs=res.inputs,
            breakdown=[b.model_dump() for b in res.breakdown],
            subtotal_pkr=res.subtotal_pkr,
            tax_pkr=res.tax_pkr,
            grand_total_pkr=res.grand_total_pkr,
            status=res.status.value,
            policy_profile=res.policy_profile,
            tariff_version=res.tariff_version,
            issues=res.issues,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(calc_record)
        session.current_state = "RESULT"
        self.db.commit()

        return format_calculation_result(res)

    def _check_edit_request(self, cmd: str) -> Optional[str]:
        if cmd in ["1", "edit 1", "edit arrival", "edit arrival date", "arrival", "arrival date"]:
            return "AWAITING_ARRIVAL_DATE"
        if cmd in ["2", "edit 2", "edit payment", "edit payment date", "payment", "payment date"]:
            return "AWAITING_PAYMENT_DATE"
        if cmd in ["3", "edit 3", "edit category", "category"]:
            return "AWAITING_CATEGORY"
        if cmd in ["4", "edit 4", "edit class", "edit cargo class", "cargo class", "class"]:
            return "AWAITING_CARGO_CLASS"
        if cmd in ["5", "edit 5", "edit weight", "weight"]:
            return "AWAITING_WEIGHT"
        if cmd in ["6", "edit 6", "edit station", "station"]:
            return "AWAITING_STATION"
        if cmd in ["7", "edit 7", "edit oversize", "oversize"]:
            return "AWAITING_OVERSIZE"
        return None

    def _handle_back(self, session: ChatSession) -> str:
        state = session.current_state
        state_order = [
            "START",
            "AWAITING_ARRIVAL_DATE",
            "AWAITING_PAYMENT_DATE",
            "AWAITING_CATEGORY",
            "AWAITING_CARGO_CLASS",
            "AWAITING_WEIGHT",
            "AWAITING_STATION",
            "AWAITING_OVERSIZE",
            "REVIEW",
            "RESULT",
        ]
        if state in state_order:
            idx = state_order.index(state)
            if idx > 1:
                session.current_state = state_order[idx - 1]
            else:
                session.current_state = "AWAITING_ARRIVAL_DATE"
        else:
            session.current_state = "AWAITING_ARRIVAL_DATE"

        return f"Returned to previous step.\n\n{self._prompt_for_state(session)}"

    def _prompt_for_state(self, session: ChatSession) -> str:
        st = session.current_state
        data = session.collected_data or {}
        if st == "AWAITING_ARRIVAL_DATE":
            return PROMPT_ARRIVAL_DATE
        if st == "AWAITING_PAYMENT_DATE":
            return PROMPT_PAYMENT_DATE
        if st == "AWAITING_CATEGORY":
            return PROMPT_CATEGORY
        if st == "AWAITING_CARGO_CLASS":
            cat = data.get("category", "AFU")
            classes = CATEGORY_CLASS_MAP.get(cat, [])
            return format_cargo_class_prompt(cat, classes)
        if st == "AWAITING_WEIGHT":
            return PROMPT_WEIGHT
        if st == "AWAITING_STATION":
            return PROMPT_STATION
        if st == "AWAITING_OVERSIZE":
            return PROMPT_OVERSIZE
        if st == "REVIEW":
            return format_review_summary(data)
        return WELCOME_MESSAGE
