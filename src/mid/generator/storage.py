"""Read and write matches as JSON lines: one Event per line, in match order."""

from pathlib import Path

from mid.models import Event


def write_match(events: list[Event], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(event.model_dump_json() + "\n")


def read_match(path: Path) -> list[Event]:
    with path.open(encoding="utf-8") as handle:
        return [Event.model_validate_json(line) for line in handle if line.strip()]
