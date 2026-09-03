"""
cipherforge/core/analyzer.py
Comprehensive, High-Accuracy Wordlist & Credential Analytics Engine.
Accurately scores Shannon entropy, exact length distributions, character frequency,
and realistic structural pattern compositions without freezing the GUI.
"""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass, field

@dataclass
class AnalysisResult:
    total_words: int = 0
    length_distribution: dict[int, int] = field(default_factory=dict)
    char_frequency: dict[str, int] = field(default_factory=dict)
    pattern_breakdown: dict[str, float] = field(default_factory=dict)
    entropy_scores: list[tuple[str, float]] = field(default_factory=list)
    avg_entropy: float = 0.0
    max_entropy: float = 0.0
    min_entropy: float = 0.0
    avg_length: float = 0.0
    strength_tiers: dict[str, int] = field(default_factory=dict)

def shannon_entropy(word: str) -> float:
    if not word:
        return 0.0
    freq = Counter(word)
    total = len(word)
    return -sum((c / total) * math.log2(c / total) for c in freq.values())

def strength_tier(entropy: float) -> str:
    if entropy < 2.0:
        return 'Weak'
    elif entropy < 3.0:
        return 'Fair'
    elif entropy < 3.8:
        return 'Strong'
    else:
        return 'Excellent'

def analyze_wordlist(wordlist: set[str] | list[str], max_eval_sample: int = 30000) -> AnalysisResult:
    result = AnalysisResult()
    if not wordlist:
        return result

    if isinstance(wordlist, set):
        word_list = list(wordlist)
    else:
        word_list = wordlist

    total = len(word_list)
    result.total_words = total

    # Exact length distribution and average length
    len_dist = Counter(len(w) for w in word_list)
    result.length_distribution = dict(sorted(len_dist.items()))
    total_chars = sum(k * v for k, v in len_dist.items())
    result.avg_length = round(total_chars / max(total, 1), 2)

    # Character frequency: count exact top characters (sample only if > 150k words for responsiveness)
    if total > 150000:
        char_sample = random.sample(word_list, 50000)
        all_chars = Counter("".join(char_sample))
    else:
        all_chars = Counter("".join(word_list))
    result.char_frequency = dict(all_chars.most_common(18))

    # Accurate, realistic password structural pattern breakdown
    pattern_sample = word_list if total <= 50000 else random.sample(word_list, 50000)
    n_sample = len(pattern_sample)

    pure_lower = 0
    capitalized = 0
    has_digit = 0
    has_special = 0
    mixed_complex = 0

    for w in pattern_sample:
        is_alpha = w.isalpha()
        is_lower = w.islower()
        has_num = any(c.isdigit() for c in w)
        has_sym = any(not c.isalnum() for c in w)
        has_let = any(c.isalpha() for c in w)

        if is_lower and is_alpha:
            pure_lower += 1
        if len(w) > 1 and w[0].isupper() and w[1:].islower():
            capitalized += 1
        if has_num:
            has_digit += 1
        if has_sym:
            has_special += 1
        if has_let and has_num and has_sym:
            mixed_complex += 1

    result.pattern_breakdown = {
        'Has Digits': round(100 * has_digit / max(n_sample, 1), 1),
        'Has Symbols': round(100 * has_special / max(n_sample, 1), 1),
        'Pure Lower': round(100 * pure_lower / max(n_sample, 1), 1),
        'Capitalized': round(100 * capitalized / max(n_sample, 1), 1),
        'Mixed Complex': round(100 * mixed_complex / max(n_sample, 1), 1),
    }

    # Shannon entropy evaluation sample (up to max_eval_sample for deep ranking)
    if total > max_eval_sample:
        entropy_sample = random.sample(word_list, max_eval_sample)
    else:
        entropy_sample = word_list

    scored = [(w, round(shannon_entropy(w), 4)) for w in entropy_sample]
    scored.sort(key=lambda x: x[1], reverse=True)

    result.entropy_scores = scored
    entropies = [e for _, e in scored]
    result.avg_entropy = round(sum(entropies) / len(entropies), 3)
    result.max_entropy = round(max(entropies), 3)
    result.min_entropy = round(min(entropies), 3)

    tiers = Counter(strength_tier(e) for _, e in scored)
    scale_tier = total / len(scored)
    result.strength_tiers = {
        'Weak': int(tiers.get('Weak', 0) * scale_tier),
        'Fair': int(tiers.get('Fair', 0) * scale_tier),
        'Strong': int(tiers.get('Strong', 0) * scale_tier),
        'Excellent': int(tiers.get('Excellent', 0) * scale_tier),
    }

    return result
