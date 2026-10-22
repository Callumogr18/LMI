import asyncio
from pathlib import Path

import mid.config as config
import mid.generator.storage as storage
import mid.models as models
from mid.ingest.validator import ingest_events
from mid.pipeline import MatchState


async def replay_match(
    match_path: Path,
    queue: asyncio.Queue[models.Event],
    settings: config.Settings,
    match_state: MatchState,
):
    """
    Replay events from match file and emit at interval specified by settings.
    
    Events emitted based on their timestamps scaled by replay speed.
    Updates MatchState if provided.
    """
    raw_events = storage.read_match(match_path)
    if not raw_events:
        print("Error: No events found in match file")
        return
    
    # Ingest: validate, deduplicate, order
    events = ingest_events(raw_events)
    print(f"Ingested {len(events)} valid events from {len(raw_events)} raw events")

    # Sort events by timestamp to handle out-of-order data
    events.sort(key=lambda e: e.ts)
    
    for i, event in enumerate(events):
        if i == 0:
            delay = 0.0
        else:
            delay = ((event.ts - events[i - 1].ts).total_seconds()) / settings.replay_speed

        if delay > 0:
            await asyncio.sleep(delay)

        await queue.put(event)
        
        if match_state:
            match_state.update(event)
        
        print(f"[{event.minute:02d}:{event.second:02d}] {event.type.value}: {event.id}")