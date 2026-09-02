"""
cipherforge/core/analyzer.py
─────────────────────────────
Post-generation analysis: entropy scoring, length distribution,
character frequency, and pattern breakdown.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field


@dataclass
class AnalysisResult:
    """Holds the full analysis of a generated wordlist."""
    total_words: int = 0
    length_distribution: dict[int, int] = field(default_factory=dict)
    char_frequency: dict[str, int] = field(default_factory=dict)
    pattern_breakdown: dict[str, float] = field(default_factory=dict)  # label → percentage
    entropy_scores: list[tuple[str, float]] = field(default_factory=list)  # (word, entropy) sorted desc
    avg_entropy: float = 0.0
    max_entropy: float = 0.0
    min_entropy: float = 0.0
    avg_length: float = 0.0
    strength_tiers: dict[str, int] = field(default_factory=dict)  # tier → count


def shannon_entropy(word: str) -> float:
    """
    Calculate Shannon entropy of a word in bits.
    Higher = more random/complex.
    """
    if not word:
        return 0.0
    freq = Counter(word)
    total = len(word)
    return -sum((c / total) * math.log2(c / total) for c in freq.values())


def strength_tier(entropy: float) -> str:
    """Classify entropy score into a human-readable tier."""
    if entropy < 2.0:
        return 'Weak'
    elif entropy < 3.0:
        return 'Fair'
    elif entropy < 3.8:
        return 'Strong'
    else:
        return 'Excellent'


def analyze_wordlist(wordlist: set[str]) -> AnalysisResult:
    """
    Run full analysis on a generated wordlist set.
    Returns an AnalysisResult dataclass ready for GUI rendering.
    """
    result = AnalysisResult()
    if not wordlist:
        return result

    result.total_words = len(wordlist)

    # ── Length Distribution ───────────────────────────────────────────────────
    len_dist: dict[int, int] = Counter(len(w) for w in wordlist)
    result.length_distribution = dict(sorted(len_dist.items()))
    result.avg_length = sum(k * v for k, v in len_dist.items()) / result.total_words

    # ── Character Frequency (top 30) ──────────────────────────────────────────
    all_chars: Counter = Counter()
    for w in wordlist:
        all_chars.update(w)
    result.char_frequency = dict(all_chars.most_common(30))

    # ── Pattern Breakdown ─────────────────────────────────────────────────────
    with_prefix    = sum(1 for w in wordlist if any(w.startswith(p) for p in ['admin_', 'user_', 'root_', 'hack_', 'pass_', 'secret_']))
    with_suffix_num= sum(1 for w in wordlist if w[-1].isdigit())
    with_leet      = sum(1 for w in wordlist if any(c in w for c in ['@', '$', '0', '1', '3', '4', '5', '7', '8', '!']))
    with_upper     = sum(1 for w in wordlist if any(c.isupper() for c in w))
    n = result.total_words

    result.pattern_breakdown = {
        'Has Prefix'         : round(100 * with_prefix     / n, 1),
        'Ends with Digit'    : round(100 * with_suffix_num / n, 1),
        'Leet Chars'         : round(100 * with_leet       / n, 1),
        'Has Uppercase'      : round(100 * with_upper      / n, 1),
    }

    # ── Entropy Scoring ───────────────────────────────────────────────────────
    # For performance, sample up to 5000 words for entropy scoring
    sample_words = list(wordlist)
    if len(sample_words) > 5000:
        import random
        random.seed(42)
        sample_words = random.sample(sample_words, 5000)

    scored = [(w, shannon_entropy(w)) for w in sample_words]
    scored.sort(key=lambda x: x[1], reverse=True)

    result.entropy_scores = scored  # all scored words, desc order
    entropies = [e for _, e in scored]
    result.avg_entropy = sum(entropies) / len(entropies)
    result.max_entropy = max(entropies)
    result.min_entropy = min(entropies)

    # ── Strength Tiers ────────────────────────────────────────────────────────
    tiers: Counter = Counter(strength_tier(e) for _, e in scored)
    result.strength_tiers = {
        'Weak':      tiers.get('Weak', 0),
        'Fair':      tiers.get('Fair', 0),
        'Strong':    tiers.get('Strong', 0),
        'Excellent': tiers.get('Excellent', 0),
    }

    return result
