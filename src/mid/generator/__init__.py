"""Seedable synthetic football match generator."""

from mid.generator.storage import read_match, write_match
from mid.generator.synthetic import generate_match

__all__ = ["generate_match", "read_match", "write_match"]
