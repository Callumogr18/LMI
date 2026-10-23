"""Closed vocabularies shared by events and narrative items."""

from enum import StrEnum


class EventType(StrEnum):
    PASS = "pass"
    SHOT = "shot"
    CARRY = "carry"
    DRIBBLE = "dribble"
    TACKLE = "tackle"
    INTERCEPTION = "interception"
    CLEARANCE = "clearance"
    FOUL = "foul"
    SAVE = "save"
    GOAL = "goal"
    CARD = "card"


class FactKind(StrEnum):
    POSSESSION_SHARE = "possession_share"
    PASS_COMPLETION = "pass_completion"
    PASS_DISTANCE = "pass_distance"
    PASS_DIFFICULTY = "pass_difficulty"
    PRESSURE = "pressure"
    TEMPO = "tempo"
    SHOT_CONVERSION = "shot_conversion"


class FactScope(StrEnum):
    HOME = "home"
    AWAY = "away"
    MATCH = "match"


class CardColor(StrEnum):
    YELLOW = "yellow"
    RED = "red"


class Outcome(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    GOAL = "goal"
    SAVED = "saved"
    BLOCKED = "blocked"
    OFF_TARGET = "off_target"
    NEUTRAL = "neutral"


class Audience(StrEnum):
    ANALYST = "analyst"
    FAN = "fan"


class Status(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    FALLBACK = "fallback"
