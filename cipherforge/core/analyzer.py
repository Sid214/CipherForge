"""
cipherforge/core/analyzer.py
Optimized post-generation and external wordlist analysis:
Fast Shannon entropy scoring, length distribution, character frequency, and pattern breakdown.
Prevents GUI freezing on large datasets.
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

def analyze_wordlist(wordlist: set[str] | list[str], max_eval_sample: int = 15000) -> AnalysisResult:
    result = AnalysisResult()
    if not wordlist:
        return result

    if isinstance(wordlist, set):
        word_list = list(wordlist)
    else:
        word_list = wordlist

    total = len(word_list)
    result.total_words = total

    # If dataset is very large (> 25000), sample for fast length & char stats
    if total > 30000:
        stat_sample = random.sample(word_list, 20000)
        len_dist = Counter(len(w) for w in stat_sample)
        scale = total / 20000
        result.length_distribution = {k: int(v * scale) for k, v in sorted(len_dist.items())}
        result.avg_length = sum(len(w) for w in stat_sample) / len(stat_sample)
        all_chars: Counter = Counter()
        for w in stat_sample:
            all_chars.update(w)
        result.char_frequency = dict(all_chars.most_common(20))
        check_words = stat_sample
    else:
        len_dist = Counter(len(w) for w in word_list)
        result.length_distribution = dict(sorted(len_dist.items()))
        result.avg_length = sum(k * v for k, v in len_dist.items()) / total
        all_chars = Counter()
        for w in word_list:
            all_chars.update(w)
        result.char_frequency = dict(all_chars.most_common(20))
        check_words = word_list

    # Pattern Breakdown
    n_sample = len(check_words)
    prefixes = ('admin_', 'user_', 'root_', 'hack_', 'pass_', 'secret_')
    leet_set = {'@', '$', '0', '1', '3', '4', '5', '7', '8', '!'}
    
    with_prefix = 0
    with_suffix_num = 0
    with_leet = 0
    with_upper = 0

    for w in check_words:
        if w.startswith(prefixes):
            with_prefix += 1
        if w and w[-1].isdigit():
            with_suffix_num += 1
        if any(c in leet_set for c in w):
            with_leet += 1
        if any(c.isupper() for c in w):
            with_upper += 1

    result.pattern_breakdown = {
        'Has Prefix': round(100 * with_prefix / n_sample, 1),
        'Ends with Digit': round(100 * with_suffix_num / n_sample, 1),
        'Leet Chars': round(100 * with_leet / n_sample, 1),
        'Has Uppercase': round(100 * with_upper / n_sample, 1),
    }

    # Entropy evaluation sample (limit to max_eval_sample for instantaneous response)
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
