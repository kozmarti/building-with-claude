"""Tools for a training log assistant.

A tool has two halves:
  1. a normal Python function that does the work (Claude never runs it; we do)
  2. a schema that tells Claude the tool exists, what it does and what
     arguments it takes

Claude reads the schemas, decides when a tool would help, and asks us to
call it. We run the function and send the result back.

The training log is stored in training_log.json next to this file.
"""

import json
from datetime import date, datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / "training_log.json"


class ToolError(Exception):
    """Raised for bad input; the message is sent back to Claude as an error."""


# --- 1. Tool functions --------------------------------------------------------

def get_current_datetime() -> dict:
    now = datetime.now()
    return {"datetime": now.isoformat(timespec="minutes"), "weekday": now.strftime("%A")}


def calculate_pace(distance_km: float, duration_minutes: float) -> dict:
    if distance_km <= 0 or duration_minutes <= 0:
        raise ToolError("distance_km and duration_minutes must both be greater than 0")
    pace = duration_minutes / distance_km
    minutes, seconds = divmod(round(pace * 60), 60)
    return {
        "pace_per_km": f"{minutes}:{seconds:02d} min/km",
        "speed_kmh": round(distance_km / (duration_minutes / 60), 2),
    }


def _load_log() -> list:
    return json.loads(LOG_FILE.read_text()) if LOG_FILE.exists() else []


def _parse_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ToolError(f"{field} must be a date in YYYY-MM-DD format, got {value!r}")


def log_workout(date: str, sport: str, duration_minutes: float,
                distance_km: float = None, notes: str = "") -> dict:
    _parse_date(date, "date")
    if duration_minutes <= 0:
        raise ToolError("duration_minutes must be greater than 0")
    entry = {"date": date, "sport": sport.lower(), "duration_minutes": duration_minutes,
             "distance_km": distance_km, "notes": notes}
    log = _load_log()
    log.append(entry)
    LOG_FILE.write_text(json.dumps(log, indent=2) + "\n")
    return {"saved": entry, "total_workouts_logged": len(log)}


def get_training_summary(start_date: str, end_date: str) -> dict:
    start, end = _parse_date(start_date, "start_date"), _parse_date(end_date, "end_date")
    if start > end:
        raise ToolError("start_date must be on or before end_date")
    workouts = [w for w in _load_log() if start <= date.fromisoformat(w["date"]) <= end]
    by_sport = {}
    for w in workouts:
        s = by_sport.setdefault(w["sport"], {"sessions": 0, "minutes": 0, "km": 0})
        s["sessions"] += 1
        s["minutes"] += w["duration_minutes"]
        s["km"] += w["distance_km"] or 0
    return {"from": start_date, "to": end_date, "workouts": len(workouts), "by_sport": by_sport}


# --- 2. Tool schemas ----------------------------------------------------------
# "strict": True makes the API guarantee Claude's arguments match the schema.
# Strict schemas need "additionalProperties": False.

TOOL_SCHEMAS = [
    {
        "name": "get_current_datetime",
        "description": "Get the current local date, time and weekday. Use it whenever "
                       "the user says 'today', 'yesterday', 'this week' and so on.",
        "strict": True,
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "calculate_pace",
        "description": "Calculate running or cycling pace (min/km) and average speed (km/h) "
                       "from a distance and a duration.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "distance_km": {"type": "number", "description": "Distance in kilometres"},
                "duration_minutes": {"type": "number", "description": "Duration in minutes"},
            },
            "required": ["distance_km", "duration_minutes"],
            "additionalProperties": False,
        },
    },
    {
        "name": "log_workout",
        "description": "Save a completed workout to the training log. Only call it when the "
                       "user describes a workout they actually did.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Workout date, YYYY-MM-DD"},
                "sport": {"type": "string", "description": "e.g. running, cycling, swimming, gym"},
                "duration_minutes": {"type": "number"},
                "distance_km": {"type": "number", "description": "Leave out if not relevant, e.g. for gym"},
                "notes": {"type": "string", "description": "How it felt, intervals, anything else"},
            },
            "required": ["date", "sport", "duration_minutes"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_training_summary",
        "description": "Summarise logged workouts between two dates (inclusive): number of "
                       "sessions, minutes and kilometres per sport.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string", "description": "YYYY-MM-DD"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["start_date", "end_date"],
            "additionalProperties": False,
        },
    },
]

TOOL_FUNCTIONS = {
    "get_current_datetime": get_current_datetime,
    "calculate_pace": calculate_pace,
    "log_workout": log_workout,
    "get_training_summary": get_training_summary,
}


def run_tool(name: str, tool_input: dict) -> tuple[str, bool]:
    """Run a tool by name. Returns (result as JSON text, is_error)."""
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"Unknown tool: {name}", True
    try:
        return json.dumps(func(**tool_input)), False
    except (ToolError, TypeError) as exc:
        return f"Error: {exc}", True
