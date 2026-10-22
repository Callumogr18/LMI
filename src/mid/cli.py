"""Thin command-line entry point: generate, replay and serve."""

import argparse
import asyncio
import sys
from pathlib import Path

from mid.config import Settings
from mid.generator import generate_match, write_match
from mid.replayer import replay_match
from mid.pipeline import MatchState

SUBCOMMANDS = {
    "generate": "Generate a seeded synthetic match file.",
    "replay": "Replay a match as a timed stream into MatchState (Phase 2).",
    "serve": "Serve the broadcast web panel (Phase 8).",
}


def build_parser():
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
        elif name == "replay":
            subparser.add_argument("--match-id", required=True, help="Match id to replay.")
            subparser.add_argument(
                "--input",
                type=Path,
                help="Input JSONL path (default: <MID_DATA_DIR>/match-<match-id>.jsonl).",
            )
    return parser


def _generate(args: argparse.Namespace, settings: Settings):
    output = args.output or settings.data_dir / f"match-{args.seed}.jsonl"
    events = generate_match(args.seed, args.match_id)
    write_match(events, output)
    print(f"wrote {len(events)} events to {output}")
    return 0


def _replay(args: argparse.Namespace, settings: Settings):
    input_path = args.input or settings.data_dir / f"{args.match_id}.jsonl"
    if not input_path.exists():
        print(f"Error: Match file not found: {input_path}")
        return 1
    
    async def run_replay():
        queue = asyncio.Queue()
        match_state = MatchState(match_id=args.match_id)
        task = asyncio.create_task(replay_match(input_path, queue, settings, match_state))
        # Consume events from queue (placeholder for downstream processing)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=1.0)
                queue.task_done()
            except asyncio.TimeoutError:
                if task.done():
                    break
        
        # Print final match state
        print(f"\nFinal Match State:")
        print(f"Score: {match_state.get_score()}")
        print(f"Home possession: {match_state.home_possession_pct:.1f}%")
        print(f"Home shots: {match_state.home_shots}, Away shots: {match_state.away_shots}")
        print(f"Home passes: {match_state.home_passes}, Away passes: {match_state.away_passes}")
    
    asyncio.run(run_replay())
    return 0


def main(argv: list[str] | None = None):
    args = build_parser().parse_args(argv)
    settings = Settings.from_env()
    if args.command == "generate":
        return _generate(args, settings)
    if args.command == "replay":
        return _replay(args, settings)
    print(f"'{args.command}' is not implemented yet (llm_backend={settings.llm_backend}).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
