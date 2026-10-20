"""Thin command-line entry point: generate, replay and serve."""

import argparse
import sys
from pathlib import Path

from mid.config import Settings
from mid.generator import generate_match, write_match

SUBCOMMANDS = {
    "generate": "Generate a seeded synthetic match file.",
    "replay": "Replay a match as a timed stream into MatchState (Phase 2).",
    "serve": "Serve the broadcast web panel (Phase 8).",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mid", description="Live Match Intelligence Desk command-line interface."
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    for name, help_text in SUBCOMMANDS.items():
        subparser = subparsers.add_parser(name, help=help_text, description=help_text)
        if name == "generate":
            subparser.add_argument("--seed", type=int, default=1, help="RNG seed (default: 1).")
            subparser.add_argument("--match-id", help="Match id (default: match-<seed>).")
            subparser.add_argument(
                "--output",
                type=Path,
                help="Output JSONL path (default: <MID_DATA_DIR>/match-<seed>.jsonl).",
            )
    return parser


def _generate(args: argparse.Namespace, settings: Settings) -> int:
    output = args.output or settings.data_dir / f"match-{args.seed}.jsonl"
    events = generate_match(args.seed, args.match_id)
    write_match(events, output)
    print(f"wrote {len(events)} events to {output}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    if args.command == "generate":
        return _generate(args, settings)
    print(f"'{args.command}' is not implemented yet (llm_backend={settings.llm_backend}).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
