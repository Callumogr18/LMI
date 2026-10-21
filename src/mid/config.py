"""Environment-driven settings: LLM backend, thresholds, cooldowns and paths."""

import os
from dotenv import load_dotenv
from dataclasses import dataclass, field
from pathlib import Path

load_dotenv()


@dataclass(frozen=True)
class Settings:
    llm_backend: str 
    data_dir: Path = field(default_factory=lambda: Path("data"))
    replay_speed: float = 1.0
    narration_cooldown_minutes: float = 3.0
    max_narrator_retries: int = 1

    def __post_init__(self) -> None:
        if self.llm_backend not in ["mock", "foundry"]:
            raise ValueError(f"llm_backend must be one of 'mock', 'foundry', got {self.llm_backend}")
        if self.replay_speed <= 0:
            raise ValueError("replay_speed must be positive")

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            llm_backend=os.environ.get("MID_LLM_BACKEND"),
            data_dir=Path(os.environ.get("MID_DATA_DIR", "data")),
            replay_speed=float(os.environ.get("MID_REPLAY_SPEED", "1.0")),
            narration_cooldown_minutes=float(
                os.environ.get("MID_NARRATION_COOLDOWN_MINUTES", "3.0")
            ),
            max_narrator_retries=int(os.environ.get("MID_MAX_NARRATOR_RETRIES", "1")),
        )
