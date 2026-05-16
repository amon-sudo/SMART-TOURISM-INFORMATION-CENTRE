"""
ItineraryGeneratorService
Core AI-powered itinerary generation engine.

Flow:
  1. Load tourist preferences (from DB + request body)
  2. Query available attractions filtered by interests / budget / accessibility
  3. Resolve avg_minutes for each attraction via the fallback chain
  4. Build a context payload and call Claude (claude-sonnet-4-20250514)
  5. Parse the structured JSON response
  6. Persist Itinerary → ItineraryDay → ItineraryDayAttraction rows
  7. Generate QR code
  8. Return the complete itinerary

Claude is asked to return ONLY a JSON object (no markdown fences).
The prompt is carefully structured so the output is deterministic
and machine-parseable on every call.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, time, timedelta
from typing   import Any

import requests

from app.extensions                        import db
from app.models.itinerary                  import Itinerary, ItineraryStatus
from app.models.itinerary_day_attraction   import ItineraryDayAttraction
from app.models.attraction_time_data       import (
    AttractionTimeData, TimeDataSource, CATEGORY_DEFAULTS,
)
from app.services.qr_code_service          import qr_code_service

# ── Constants ─────────────────────────────────────────────────────────────────
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"
CLAUDE_MODEL   = "claude-sonnet-4-20250514"
MAX_TOKENS     = 4096

# Usable touring hours per day: 09:00 – 18:00 = 540 minutes
# Subtract ~90 min for travel/meals buffer
AVAILABLE_MINUTES_PER_DAY = 450
DAY_START_HOUR            = 9    # 09:00

# Budget ceiling mapping (KES)
BUDGET_CEILINGS = {
    "low":    500,
    "medium": 2000,
    "high":   999_999,
}


class ItineraryGeneratorService:

    # ── Public entry point ────────────────────────────────────────────────────

    def generate(
        self,
        user_id,
        duration_days: int,
        interests: list[str],
        budget_level: str,
        pace: str,
        accessibility_required: bool,
        destination: str,
        language: str = "en",
        kiosk_id=None,
    ) -> Itinerary:
        """
        Generate and persist a complete itinerary for a tourist.

        Args:
            user_id              : UUID of the authenticated tourist
            duration_days        : Number of days (e.g. 5)
            interests            : List of attraction categories e.g. ['wildlife','museum']
            budget_level         : 'low' | 'medium' | 'high'
            pace                 : 'relaxed' | 'moderate' | 'intensive'
            accessibility_required: If True, filter to wheelchair-accessible only
            destination          : Destination name for narrative context e.g. 'Nairobi'
            language             : ISO 639-1 code for narrative language
            kiosk_id             : UUID of originating kiosk (optional)

        Returns:
            Persisted Itinerary with all days and attractions loaded
        """
        # ── 1. Load candidate attractions ─────────────────────────────────────
        attractions = self._query_attractions(
            interests=interests,
            budget_level=budget_level,
            accessibility_required=accessibility_required,
        )

        if not attractions:
            raise ValueError(
                "No attractions found matching the given preferences. "
                "Please broaden your interests or adjust the budget."
            )

        # ── 2. Resolve avg_minutes for each attraction ─────────────────────────
        enriched = self._enrich_with_time_data(attractions)

        # ── 3. Build Claude prompt ─────────────────────────────────────────────
        prompt = self._build_prompt(
            duration_days=duration_days,
            interests=interests,
            budget_level=budget_level,
            pace=pace,
            accessibility_required=accessibility_required,
            destination=destination,
            language=language,
            attractions=enriched,
        )

        # ── 4. Call Claude ─────────────────────────────────────────────────────
        claude_response = self._call_claude(prompt)

        # ── 5. Parse response ──────────────────────────────────────────────────
        plan = self._parse_response(claude_response)

        # ── 6. Persist everything ──────────────────────────────────────────────
        itinerary = self._persist(
            user_id=user_id,
            kiosk_id=kiosk_id,
            plan=plan,
            enriched_attractions=enriched,
            destination=destination,
            duration_days=duration_days,
        )

        # ── 7. Generate QR code ────────────────────────────────────────────────
        qr = qr_code_service.generate_or_refresh(
            target_type="itinerary",
            target_id=itinerary.id,
            created_by=user_id,
        )
        itinerary.qr_code_url = qr.url
        db.session.commit()

        return itinerary

    # ── Step 1: Query attractions ──────────────────────────────────────────────

    def _query_attractions(
        self,
        interests: list[str],
        budget_level: str,
        accessibility_required: bool,
    ) -> list:
        """
        Query approved attractions matching the tourist's filters.
        Returns raw ORM Attraction objects.
        """
        from app.models.attraction import Attraction   # local import to avoid circular

        budget_ceiling = BUDGET_CEILINGS.get(budget_level, BUDGET_CEILINGS["medium"])

        query = (
            Attraction.query
            .filter(Attraction.status == "approved")
            .filter(Attraction.category.in_(interests))
            .filter(
                db.or_(
                    Attraction.ticket_fee == None,
                    Attraction.ticket_fee <= budget_ceiling,
                )
            )
        )

        if accessibility_required:
            query = query.filter(Attraction.is_wheelchair_accessible == True)

        # Order by rating descending so Claude gets the best options first
        query = query.order_by(Attraction.rating.desc().nullslast())

        return query.all()

    # ── Step 2: Enrich with time data ──────────────────────────────────────────

    def _enrich_with_time_data(self, attractions: list) -> list[dict]:
        """
        For each attraction, resolve avg_minutes via the fallback chain.
        Returns a list of dicts ready to be included in the Claude prompt.

        Fallback chain:
          analytics (samples >= 10, confidence >= 0.5)
          → operator_input (confidence >= 0.7)
          → analytics (any)
          → ai_estimate (any stored)
          → inline Claude estimate (requested inside the main prompt)
        """
        enriched = []

        for attr in attractions:
            best = AttractionTimeData.best_for(attr.id)

            if best:
                avg_minutes   = best.avg_minutes
                time_source   = best.source.value
                time_confidence = best.confidence
            else:
                # No stored data — mark for inline Claude estimation
                category_default = CATEGORY_DEFAULTS.get(
                    attr.category, CATEGORY_DEFAULTS["default"]
                )
                avg_minutes     = None          # Claude will estimate this
                time_source     = "unknown"
                time_confidence = 0.0

            enriched.append({
                "id":                    str(attr.id),
                "name":                  attr.name,
                "category":              attr.category,
                "description":           attr.description or "",
                "location":              attr.location or "",
                "ticket_fee":            float(attr.ticket_fee) if attr.ticket_fee else 0,
                "rating":                float(attr.rating) if attr.rating else None,
                "is_wheelchair_accessible": attr.is_wheelchair_accessible,
                "avg_minutes":           avg_minutes,       # None = Claude estimates
                "time_source":           time_source,
                "time_confidence":       time_confidence,
                # Hint Claude uses when avg_minutes is None
                "category_default_minutes": CATEGORY_DEFAULTS.get(
                    attr.category, CATEGORY_DEFAULTS["default"]
                ),
            })

        return enriched

    # ── Step 3: Build Claude prompt ────────────────────────────────────────────

    def _build_prompt(
        self,
        duration_days: int,
        interests: list[str],
        budget_level: str,
        pace: str,
        accessibility_required: bool,
        destination: str,
        language: str,
        attractions: list[dict],
    ) -> str:
        """
        Build the structured system + user prompt sent to Claude.
        The system prompt is strict about JSON-only output.
        """
        pace_description = {
            "relaxed":   "2–3 attractions per day with generous breaks",
            "moderate":  "3–4 attractions per day with short breaks",
            "intensive": "4–5 attractions per day, back-to-back",
        }.get(pace, "3–4 attractions per day")

        # Identify which attractions have missing time data
        missing_time = [a for a in attractions if a["avg_minutes"] is None]
        missing_note = ""
        if missing_time:
            missing_names = ", ".join(a["name"] for a in missing_time)
            missing_note  = (
                f"\n\nIMPORTANT: The following attractions have no visit duration data: "
                f"{missing_names}. "
                f"For each of these, you MUST estimate a realistic avg_minutes value "
                f"based on their category and description. Use the category_default_minutes "
                f"field as a starting point but adjust based on description complexity. "
                f"Include your estimated value in the attraction object in the response."
            )

        system_prompt = (
            "You are a tourism itinerary planning engine for the Kenya Digital Smart Tourism "
            "Information Centre. Your output must be ONLY a valid JSON object — no markdown "
            "fences, no preamble, no explanation. Any non-JSON output will cause a system error.\n\n"
            "The JSON must follow this exact schema:\n"
            "{\n"
            '  "title": "string — evocative itinerary title",\n'
            '  "summary": "string — 2-3 sentence overview of the full trip",\n'
            '  "days": [\n'
            "    {\n"
            '      "day_number": integer,\n'
            '      "day_title": "string — short title for this day e.g. \'Wildlife Morning\'",\n'
            '      "narrative": "string — 2-4 sentence flowing description of the day",\n'
            '      "attractions": [\n'
            "        {\n"
            '          "attraction_id": "uuid string — MUST match an id from the provided list",\n'
            '          "visit_order": integer starting at 1,\n'
            '          "start_time": "HH:MM — 24-hour format",\n'
            '          "duration_minutes": integer — use provided avg_minutes, or your estimate if null,\n'
            '          "narrative_note": "string — 1-2 sentences about this specific stop"\n'
            "        }\n"
            "      ]\n"
            "    }\n"
            "  ]\n"
            "}\n\n"
            "Rules:\n"
            "- Schedule starts at 09:00 each day\n"
            "- Leave at least 30 minutes between attractions for travel\n"
            "- Do not exceed 18:00 (end of day)\n"
            "- Spread attractions logically — group nearby locations on the same day\n"
            "- Never repeat the same attraction across days\n"
            "- Only use attraction_ids from the provided list\n"
            f"- Write all narrative text in language code: {language}\n"
            "- Respect the tourist's pace setting\n"
        )

        user_prompt = (
            f"Generate a {duration_days}-day itinerary for a tourist visiting {destination}.\n\n"
            f"Tourist profile:\n"
            f"  - Interests: {', '.join(interests)}\n"
            f"  - Budget: {budget_level}\n"
            f"  - Pace: {pace} ({pace_description})\n"
            f"  - Accessibility required: {'yes' if accessibility_required else 'no'}\n"
            f"  - Available time per day: 09:00–18:00\n"
            f"{missing_note}\n\n"
            f"Available attractions (use ONLY these — do not invent new ones):\n"
            f"{json.dumps(attractions, indent=2, default=str)}\n\n"
            f"Return the itinerary JSON now."
        )

        return json.dumps({
            "system": system_prompt,
            "user":   user_prompt,
        })

    # ── Step 4: Call Claude API ────────────────────────────────────────────────

    def _call_claude(self, prompt_json: str) -> str:
        """
        Call the Claude API and return the raw text response.
        Raises RuntimeError on API failure.
        """
        prompts = json.loads(prompt_json)

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY environment variable is not set. "
                "Add it to your .env file."
            )

        headers = {
            "Content-Type":      "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model":      CLAUDE_MODEL,
            "max_tokens": MAX_TOKENS,
            "system":     prompts["system"],
            "messages": [
                {"role": "user", "content": prompts["user"]}
            ],
        }

        try:
            response = requests.post(
                CLAUDE_API_URL,
                headers=headers,
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout:
            raise RuntimeError("Claude API request timed out after 60 seconds")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Claude API request failed: {e}")

        data = response.json()

        # Extract text from the response content blocks
        text_blocks = [
            block["text"]
            for block in data.get("content", [])
            if block.get("type") == "text"
        ]
        if not text_blocks:
            raise RuntimeError("Claude returned an empty response")

        return "".join(text_blocks)

    # ── Step 5: Parse Claude response ─────────────────────────────────────────

    def _parse_response(self, raw: str) -> dict:
        """
        Parse and validate the JSON response from Claude.
        Strips accidental markdown fences if Claude adds them despite instructions.
        Raises ValueError with a clear message if the schema is wrong.
        """
        # Strip markdown fences defensively
        clean = raw.strip()
        if clean.startswith("```"):
            lines = clean.split("\n")
            # Remove first and last fence lines
            clean = "\n".join(
                line for line in lines
                if not line.strip().startswith("```")
            ).strip()

        try:
            plan = json.loads(clean)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Claude returned invalid JSON: {e}\n"
                f"Raw response (first 500 chars): {raw[:500]}"
            )

        # ── Schema validation ──────────────────────────────────────────────────
        required_top = {"title", "summary", "days"}
        missing = required_top - set(plan.keys())
        if missing:
            raise ValueError(f"Claude response missing required fields: {missing}")

        if not isinstance(plan["days"], list) or len(plan["days"]) == 0:
            raise ValueError("Claude response 'days' must be a non-empty list")

        for day in plan["days"]:
            required_day = {"day_number", "day_title", "narrative", "attractions"}
            missing_day  = required_day - set(day.keys())
            if missing_day:
                raise ValueError(
                    f"Day {day.get('day_number')} missing fields: {missing_day}"
                )

            for stop in day["attractions"]:
                required_stop = {
                    "attraction_id", "visit_order",
                    "start_time", "duration_minutes", "narrative_note"
                }
                missing_stop = required_stop - set(stop.keys())
                if missing_stop:
                    raise ValueError(
                        f"Attraction stop missing fields: {missing_stop}"
                    )

        return plan

    # ── Step 6: Persist ────────────────────────────────────────────────────────

    def _persist(
        self,
        user_id,
        kiosk_id,
        plan: dict,
        enriched_attractions: list[dict],
        destination: str,
        duration_days: int,
    ) -> Itinerary:
        """
        Write Itinerary → ItineraryDay → ItineraryDayAttraction to the DB
        in a single transaction.

        Also back-fills AttractionTimeData with AI estimates for any
        attraction whose avg_minutes was None (Claude estimated them inline).
        """
        from app.models.itinerary_day import ItineraryDay  # avoid circular

        # Build a lookup: attraction_id → enriched dict
        attraction_lookup = {a["id"]: a for a in enriched_attractions}

        try:
            # ── Itinerary ──────────────────────────────────────────────────────
            itinerary = Itinerary(
                user_id=user_id,
                title=plan["title"],
                status=ItineraryStatus.PUBLISHED,   # auto-generated = directly published
            )
            db.session.add(itinerary)
            db.session.flush()

            # ── Days ───────────────────────────────────────────────────────────
            for day_data in plan["days"]:
                iday = ItineraryDay(
                    itinerary_id=itinerary.id,
                    day_number=day_data["day_number"],
                    title=day_data.get("day_title", f"Day {day_data['day_number']}"),
                    narrative=day_data.get("narrative", ""),
                )
                db.session.add(iday)
                db.session.flush()

                # ── Day attractions ────────────────────────────────────────────
                for stop in day_data["attractions"]:
                    attraction_id  = stop["attraction_id"]
                    duration_mins  = int(stop["duration_minutes"])
                    start_t        = self._parse_time(stop["start_time"])

                    db.session.add(ItineraryDayAttraction(
                        itinerary_day_id=iday.id,
                        attraction_id=uuid.UUID(attraction_id),
                        visit_order=stop["visit_order"],
                        start_time=start_t,
                        duration_minutes=duration_mins,
                        narrative_note=stop.get("narrative_note"),
                    ))

                    # Back-fill AI estimate into AttractionTimeData if unknown
                    enriched = attraction_lookup.get(attraction_id, {})
                    if enriched.get("time_source") == "unknown":
                        existing_ai = AttractionTimeData.query.filter_by(
                            attraction_id=attraction_id,
                            source=TimeDataSource.AI_ESTIMATE,
                        ).first()
                        if not existing_ai:
                            db.session.add(AttractionTimeData(
                                attraction_id=uuid.UUID(attraction_id),
                                avg_minutes=duration_mins,
                                source=TimeDataSource.AI_ESTIMATE,
                                confidence=0.3,
                                sample_count=0,
                            ))

            db.session.commit()

        except Exception:
            db.session.rollback()
            raise

        # Reload with relationships
        db.session.refresh(itinerary)
        return itinerary

    # ── Helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _parse_time(time_str: str) -> time:
        """Parse 'HH:MM' or 'HH:MM:SS' into a datetime.time object."""
        parts = time_str.strip().split(":")
        return time(int(parts[0]), int(parts[1]))


# Module-level singleton
itinerary_generator_service = ItineraryGeneratorService()
