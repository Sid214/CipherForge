"""
cipherforge/core/generator.py
──────────────────────────────
Core wordlist generation engine.

Pipeline stages:
  1. build_base_candidates()  → seed token combinations from profile fields
  2. expand_variants()        → case transformations + bounded leet substitutions
  3. apply_affixes()          → cartesian product with PREFIXES × SUFFIXES
  4. run_pipeline()           → orchestrates everything, emits progress via callback
"""

from __future__ import annotations

import itertools
import time
import datetime
import os
from typing import Callable

from .rules import (
    LEET_MAP, PREFIXES, SUFFIXES, SPECIALS,
    DEFAULT_LEET_MAX, DEFAULT_MIN_LEN, DEFAULT_MAX_LEN,
)


# ── Stage 1: Build structural seed combinations ───────────────────────────────

def build_base_candidates(profile: dict) -> set[str]:
    """
    Constructs high-probability structural root combinations from profile tokens.
    Applies no case or leet transformations — those happen in Stage 2.

    Returns a set of plain lowercase strings that serve as generation seeds.
    """
    name  = (profile.get('name')  or '').strip().lower()
    year  = (profile.get('year')  or '').strip()
    last  = (profile.get('last')  or '').strip().lower()
    pet   = (profile.get('pet')   or '').strip().lower()
    city  = (profile.get('city')  or '').strip().lower()
    color = (profile.get('color') or '').strip().lower()
    sport = (profile.get('sport') or '').strip().lower()

    year_short = year[2:] if len(year) == 4 else ''
    roots: set[str] = set()

    # ── Single tokens ─────────────────────────────────────────────────────────
    for t in filter(None, [name, last, pet, city, color, sport]):
        roots.add(t)

    # ── Name + Year variants ──────────────────────────────────────────────────
    if name and year:
        roots.add(name + year)
        if year_short:
            roots.add(name + year_short)

    # ── Name + Last ───────────────────────────────────────────────────────────
    if name and last:
        roots.add(name + last)
        roots.add(last + name)
        if year:
            roots.add(name + last + year)
            roots.add(last + name + year)

    # ── Name + Pet ────────────────────────────────────────────────────────────
    if name and pet:
        roots.add(name + pet)
        roots.add(pet + name)
        if year:
            roots.add(name + pet + year)
            roots.add(pet + name + year)
            if year_short:
                roots.add(name + pet + year_short)

    # ── Pet + Year ────────────────────────────────────────────────────────────
    if pet and year:
        roots.add(pet + year)
        if year_short:
            roots.add(pet + year_short)

    # ── Name + City + Year ────────────────────────────────────────────────────
    if name and city:
        roots.add(name + city)
        if year:
            roots.add(name + city + year)
            if year_short:
                roots.add(name + city + year_short)

    # ── Name + Color / Sport ──────────────────────────────────────────────────
    for extra in filter(None, [color, sport]):
        if name:
            roots.add(name + extra)
        if year:
            roots.add(extra + year)

    # ── Name + Special + Year (john@1990, john!1990, ...) ────────────────────
    if name and year:
        for sp in SPECIALS:
            roots.add(name + sp + year)
            if year_short:
                roots.add(name + sp + year_short)

    # ── All non-empty tokens concatenated ─────────────────────────────────────
    all_tokens = [t for t in [name, last, pet, city, color, sport, year] if t]
    if len(all_tokens) >= 3:
        roots.add(''.join(all_tokens))

    return roots


# ── Stage 2: Expand each root with case + leet variants ───────────────────────

def _case_variants(word: str) -> set[str]:
    """Return all 5 case transformations of a word."""
    return {
        word.lower(),
        word.upper(),
        word.capitalize(),
        ''.join(c.lower() if i % 2 == 0 else c.upper() for i, c in enumerate(word)),
        ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(word)),
    }


def _leet_variants(word: str, max_variants: int = DEFAULT_LEET_MAX) -> set[str]:
    """
    Generate leet-speak substitutions using itertools.product with islice guard.
    Only alphabetic-position characters are substituted; digits/specials pass through.
    """
    word_l = word.lower()
    char_options: list[list[str]] = []
    for c in word_l:
        if c in LEET_MAP:
            char_options.append([c] + LEET_MAP[c])
        else:
            char_options.append([c])

    res: set[str] = set()
    for combo in itertools.islice(itertools.product(*char_options), max_variants):
        res.add(''.join(combo))
    return res


def expand_variants(roots: set[str], leet_max: int = DEFAULT_LEET_MAX) -> set[str]:
    """
    Expand every root with:
    - 5 case transformations
    - Up to leet_max leet permutations (applied to the lowercase version)
    """
    expanded: set[str] = set()
    for root in roots:
        expanded.update(_case_variants(root))
        expanded.update(_leet_variants(root, leet_max))
    return expanded


# ── Stage 3: Apply prefix × suffix cartesian product ─────────────────────────

def apply_affixes(
    roots: set[str],
    min_len: int = DEFAULT_MIN_LEN,
    max_len: int = DEFAULT_MAX_LEN,
    extra_suffixes: list[str] | None = None,
) -> set[str]:
    """
    Cartesian-product every root with PREFIXES × SUFFIXES,
    filtering to [min_len, max_len] inclusive.
    Returns the full deduplicated wordlist set.
    """
    suffixes = list(SUFFIXES)
    if extra_suffixes:
        for s in extra_suffixes:
            if s not in suffixes:
                suffixes.append(s)

    pref_suff = list(itertools.product(PREFIXES, suffixes))
    wordlist: set[str] = set()
    for root in roots:
        for p, s in pref_suff:
            candidate = p + root + s
            if min_len <= len(candidate) <= max_len:
                wordlist.add(candidate)
    return wordlist


# ── Stage 4: Full pipeline ────────────────────────────────────────────────────

def estimate_count(profile: dict, leet_max: int = DEFAULT_LEET_MAX) -> int:
    """
    Fast upper-bound estimate without actually generating words.
    Used by the --count CLI flag and the GUI 'Estimate' button.
    """
    roots = build_base_candidates(profile)
    # Average expansion factor: ~5 case + leet_max leet, but many overlap
    # Conservative estimate: roots * avg_expansion
    estimated_roots = len(roots) * min(leet_max, 20)
    return estimated_roots * len(PREFIXES) * len(SUFFIXES)


def run_pipeline(
    profile: dict,
    progress_cb: Callable[[dict], None] | None = None,
    stop_event=None,
    leet_max: int = DEFAULT_LEET_MAX,
    min_len: int = DEFAULT_MIN_LEN,
    max_len: int = DEFAULT_MAX_LEN,
    output_path: str | None = None,
) -> dict:
    """
    Full three-stage generation pipeline with progress callbacks.

    Args:
        profile:      Dict with keys: name, last, year, pet, city, color, sport
        progress_cb:  Called with progress dicts: {stage, detail, pct}
        stop_event:   threading.Event — generator checks this for cancellation
        leet_max:     Max leet variants per root
        min_len:      Minimum word length filter
        max_len:      Maximum word length filter
        output_path:  If given, writes to this file. Auto-generates name if None.

    Returns dict:
        {count, elapsed, rate, file, sample_words, bases_count, roots_count, aborted}
    """
    def emit(stage: str, detail: str, pct: float = 0.0):
        if progress_cb:
            progress_cb({'stage': stage, 'detail': detail, 'pct': pct})

    start = time.time()
    aborted = False

    # ── Stage 1 ──────────────────────────────────────────────────────────────
    emit('stage1', 'Building structural seed combinations…', 0.05)
    bases = build_base_candidates(profile)
    emit('stage1', f'Seed roots: {len(bases)} structural patterns', 0.15)

    if stop_event and stop_event.is_set():
        return _partial_result(set(), start, output_path, bases, 0, True)

    # ── Stage 2 ──────────────────────────────────────────────────────────────
    emit('stage2', 'Expanding case & leet permutations…', 0.20)
    expanded = expand_variants(bases, leet_max)
    emit('stage2', f'Expanded: {len(expanded):,} variant roots', 0.40)

    if stop_event and stop_event.is_set():
        return _partial_result(set(), start, output_path, bases, len(expanded), True)

    # ── Stage 3 ──────────────────────────────────────────────────────────────
    emit('stage3', f'Applying {len(PREFIXES)} prefixes × {len(SUFFIXES)} suffixes…', 0.45)

    # Dynamic suffix injection: add the actual birth year & short year
    year = (profile.get('year') or '').strip()
    extra_sfx = []
    if year and year not in SUFFIXES:
        extra_sfx.append(year)
    if len(year) == 4 and year[2:] not in SUFFIXES:
        extra_sfx.append(year[2:])

    wordlist = apply_affixes(expanded, min_len, max_len, extra_sfx)
    emit('stage3', f'Filtered wordlist: {len(wordlist):,} unique words', 0.85)

    if stop_event and stop_event.is_set():
        aborted = True

    # ── Save ──────────────────────────────────────────────────────────────────
    if wordlist:
        emit('saving', 'Writing wordlist to disk…', 0.90)
        out_file = output_path or _auto_filename()
        try:
            with open(out_file, 'w', encoding='utf-8') as f:
                for w in sorted(wordlist):
                    f.write(w + '\n')
            abs_path = os.path.abspath(out_file)
        except Exception as e:
            abs_path = output_path or 'ERROR'
            emit('error', f'File write error: {e}', 0.90)
    else:
        abs_path = ''

    elapsed = max(time.time() - start, 0.001)
    sample = sorted(list(wordlist))[:25]

    emit('done', f'Complete — {len(wordlist):,} words in {elapsed:.2f}s', 1.0)

    return {
        'count':       len(wordlist),
        'elapsed':     elapsed,
        'rate':        int(len(wordlist) / elapsed),
        'file':        abs_path,
        'sample_words': sample,
        'bases_count': len(bases),
        'roots_count': len(expanded),
        'aborted':     aborted,
        'wordlist':    wordlist,   # kept in memory for analyzer
    }


def _auto_filename() -> str:
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'cipherforge_{ts}.txt'


def _partial_result(
    wordlist: set, start: float, output_path, bases, roots: int, aborted: bool
) -> dict:
    return {
        'count': 0, 'elapsed': time.time() - start,
        'rate': 0, 'file': '', 'sample_words': [],
        'bases_count': len(bases) if bases else 0,
        'roots_count': roots, 'aborted': aborted, 'wordlist': wordlist,
    }
