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
