"""
cipherforge/core/rules.py
─────────────────────────
Central constants for all generation rules.
Modify here to change app-wide behaviour without touching generator logic.
"""

# Leetspeak character substitutions
LEET_MAP: dict[str, list[str]] = {
    'a': ['@', '4'],
    'e': ['3', '€'],
    'i': ['1', '!'],
    'o': ['0', '°'],
    's': ['$', '5'],
    't': ['7', '+'],
    'b': ['8'],
    'g': ['9'],
    'l': ['1'],
    'z': ['2'],
}

# Prefix tokens to prepend
PREFIXES: list[str] = [
    "", "admin_", "user_", "root_", "hack_", "pass_", "secret_",
]

# Suffix tokens to append
SUFFIXES: list[str] = [
    "", "123", "007", "69", "420",
    "2024", "2025", "2026",
    "!", "@", "#", "$", "%", "&", "*", "?", ".",
    "1990", "90", "2000", "00",
]

# Special characters used in name+special+year combos
SPECIALS: list[str] = ['!', '@', '#', '$', '%', '&', '*', '?', '.']

# Available case transformation mode names (for documentation)
CASE_MODES: list[str] = ["lowercase", "UPPERCASE", "Capitalized", "aLtErNaTiNg", "ALtErNaTiNg"]

# Maximum number of leet permutations to generate per root to prevent explosion
DEFAULT_LEET_MAX: int = 80

# Default length bounds
DEFAULT_MIN_LEN: int = 6
DEFAULT_MAX_LEN: int = 20
