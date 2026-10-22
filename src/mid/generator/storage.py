"""Read and write matches as JSON lines: one Event per line, in match order."""

from pathlib import Path

from mid.models import Event


def write_match(events: list[Event], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for event in events:
            handle.write(event.model_dump_json() + "\n")


def read_match(path: Path) -> list[Event]:
    events = []
    with open(path, encoding="utf-8") as handle:
        for line_num, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                events.append(Event.model_validate_json(line))
            except Exception as e:
                print(f"Warning: Failed to parse line {line_num}: {e}")
    return events
