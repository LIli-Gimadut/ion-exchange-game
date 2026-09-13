"""Доменная логика химии: ионы, вещества, растворимость, движок РИО.

Не зависит от pygame и не требует окна — всё тестируется headless.
"""

from chemistry.ions import Ion, ION
from chemistry.substances import Substance, SUBSTANCES, by_id
from chemistry.solubility import solubility, Solub
from chemistry.reactions import react, ReactionResult, Effect, compound_formula
from chemistry.describe import (
    describe_result, precipitate_color, precipitate_is_colored,
)

__all__ = [
    "Ion",
    "ION",
    "Substance",
    "SUBSTANCES",
    "by_id",
    "solubility",
    "Solub",
    "react",
    "ReactionResult",
    "Effect",
    "compound_formula",
    "describe_result",
    "precipitate_color",
    "precipitate_is_colored",
]
