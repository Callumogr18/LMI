import os
from collections.abc import Iterable

from dotenv import load_dotenv

from mid.models import Event, EventType, Outcome

load_dotenv()

PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0


def ingest_events(events: Iterable[Event]) -> list[Event]:
    """
    Process raw events through validation, deduplication, ordering, and plausibility checks.
    
    Returns a clean, ordered list of valid events.
    """
    # Deduplicate by ID
    seen_ids = set()
    unique_events = []
    for event in events:
        if event.id not in seen_ids:
            seen_ids.add(event.id)
            unique_events.append(event)
    
    # Validate and filter
    valid_events = [e for e in unique_events if _is_valid(e)]
    
    # Sort by timestamp
    valid_events.sort(key=lambda e: e.ts)
    
    return valid_events


def _is_valid(event: Event) -> bool:
    # Check event for schema violations and plausibility issues
    # Pydantic already validates required fields and types
    
    # Coordinate plausibility
    if event.x is not None and not (0 <= event.x <= PITCH_LENGTH):
        return False
    if event.y is not None and not (0 <= event.y <= PITCH_WIDTH):
        return False
    if event.end_x is not None and not (0 <= event.end_x <= PITCH_LENGTH):
        return False
    if event.end_y is not None and not (0 <= event.end_y <= PITCH_WIDTH):
        return False
    
    # Event type/outcome consistency
    if event.type == EventType.SHOT and event.outcome not in (
        Outcome.GOAL, Outcome.SAVED, Outcome.BLOCKED, Outcome.OFF_TARGET
    ):
        return False
    
    if event.type == EventType.PASS and event.outcome not in (
        Outcome.SUCCESS, Outcome.FAILURE
    ):
        return False
    
    if event.type == EventType.GOAL and event.outcome is not None:
        return False
    
    if event.type == EventType.SAVE and event.outcome is not None:
        return False
    
    return True


def quality_log(event: Event) -> None:
    """
    Log quality issues for debugging
    """
    debug_dir = os.getenv("DEBUG_DIR")
    if debug_dir:
        with open(os.path.join(debug_dir, "quality_issues.log"), "a") as f:
            f.write(f"[DEBUG] {event.id}: {event.minute}:{event.second} - {event.type}\n")
    else:
        raise ValueError("DEBUG_DIR not set")
        
