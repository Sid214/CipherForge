"""
cipherforge/core/generator.py
Core wordlist generation engine with dynamic profile, family members, custom phrases, and dedicated output directories.
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

OUTPUT_DIR_NAME = "generated_wordlists"

def get_output_dir(base_dir: str | None = None) -> str:
    root = base_dir or os.getcwd()
    out_dir = os.path.join(root, OUTPUT_DIR_NAME)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir

def build_base_candidates(profile: dict) -> set[str]:
    name   = (profile.get('name')   or '').strip().lower()
    year   = (profile.get('year')   or '').strip()
    last   = (profile.get('last')   or '').strip().lower()
    pet    = (profile.get('pet')    or '').strip().lower()
    city   = (profile.get('city')   or '').strip().lower()
    color  = (profile.get('color')  or '').strip().lower()
    sport  = (profile.get('sport')  or '').strip().lower()

    # Family members list
    family_members = [m.strip().lower() for m in profile.get('family_members', []) if m and m.strip()]
    # Custom phrases / passwords
    custom_phrases = [p.strip().lower() for p in profile.get('custom_phrases', []) if p and p.strip()]

    year_short = year[2:] if len(year) == 4 else ''
    roots: set[str] = set()

    # 1. Single tokens
    primary_tokens = [name, last, pet, city, color, sport] + family_members + custom_phrases
    for t in filter(None, primary_tokens):
        roots.add(t)

    # 2. Name + Year variants
    if name and year:
        roots.add(name + year)
        if year_short:
            roots.add(name + year_short)

    # 3. Name + Last
    if name and last:
        roots.add(name + last)
        roots.add(last + name)
        if year:
            roots.add(name + last + year)
            roots.add(last + name + year)

    # 4. Name + Pet
    if name and pet:
        roots.add(name + pet)
        roots.add(pet + name)
        if year:
            roots.add(name + pet + year)
            roots.add(pet + name + year)
            if year_short:
                roots.add(name + pet + year_short)

    # 5. Pet + Year
    if pet and year:
        roots.add(pet + year)
        if year_short:
            roots.add(pet + year_short)

    # 6. Name + City + Year
    if name and city:
        roots.add(name + city)
        if year:
            roots.add(name + city + year)
            if year_short:
                roots.add(name + city + year_short)

    # 7. Name + Color / Sport
    for extra in filter(None, [color, sport]):
        if name:
            roots.add(name + extra)
        if year:
            roots.add(extra + year)

    # 8. Family member combinations
    for member in family_members:
        roots.add(member)
        if year:
            roots.add(member + year)
            if year_short:
                roots.add(member + year_short)
        if name:
            roots.add(name + member)
            roots.add(member + name)
            if year:
                roots.add(name + member + year)
        if last:
            roots.add(member + last)
            if year:
                roots.add(member + last + year)

    # 9. Custom phrases combinations
    for phrase in custom_phrases:
        roots.add(phrase)
        # remove spaces if any
        nospace = phrase.replace(" ", "")
        if nospace:
            roots.add(nospace)
        if year:
            roots.add(nospace + year)
            if year_short:
                roots.add(nospace + year_short)
        if name:
            roots.add(name + nospace)
            roots.add(nospace + name)

    # 10. Name + Special + Year (john@1990, john!1990, ...)
    if name and year:
        for sp in SPECIALS:
            roots.add(name + sp + year)
            if year_short:
                roots.add(name + sp + year_short)

    # 11. All non-empty tokens concatenated
    all_tokens = [t for t in [name, last, pet, city, color, sport, year] if t]
    if len(all_tokens) >= 3:
        roots.add(''.join(all_tokens))

    return roots

def _case_variants(word: str) -> set[str]:
    return {
        word.lower(),
        word.upper(),
        word.capitalize(),
        ''.join(c.lower() if i % 2 == 0 else c.upper() for i, c in enumerate(word)),
        ''.join(c.upper() if i % 2 == 0 else c.lower() for i, c in enumerate(word)),
    }

def _leet_variants(word: str, max_variants: int = DEFAULT_LEET_MAX) -> set[str]:
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
    expanded: set[str] = set()
    for root in roots:
        expanded.update(_case_variants(root))
        expanded.update(_leet_variants(root, leet_max))
    return expanded

def apply_affixes(
    roots: set[str],
    min_len: int = DEFAULT_MIN_LEN,
    max_len: int = DEFAULT_MAX_LEN,
    extra_suffixes: list[str] | None = None,
) -> set[str]:
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

def estimate_count(profile: dict, leet_max: int = DEFAULT_LEET_MAX) -> int:
    roots = build_base_candidates(profile)
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
    def emit(stage: str, detail: str, pct: float = 0.0):
        if progress_cb:
            progress_cb({'stage': stage, 'detail': detail, 'pct': pct})

    start = time.time()
    aborted = False

    emit('stage1', 'Building structural seed combinations...', 0.05)
    bases = build_base_candidates(profile)
    emit('stage1', f'Seed roots: {len(bases)} structural patterns', 0.15)

    if stop_event and stop_event.is_set():
        return _partial_result(set(), start, output_path, bases, 0, True)

    emit('stage2', 'Expanding case & leet permutations...', 0.20)
    expanded = expand_variants(bases, leet_max)
    emit('stage2', f'Expanded: {len(expanded):,} variant roots', 0.40)

    if stop_event and stop_event.is_set():
        return _partial_result(set(), start, output_path, bases, len(expanded), True)

    emit('stage3', f'Applying {len(PREFIXES)} prefixes x {len(SUFFIXES)} suffixes...', 0.45)

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

    if wordlist:
        emit('saving', 'Writing wordlist to disk...', 0.90)
        out_dir = get_output_dir()
        if output_path:
            if os.path.isabs(output_path):
                out_file = output_path
            else:
                out_file = os.path.join(out_dir, os.path.basename(output_path))
        else:
            out_file = os.path.join(out_dir, _auto_filename())

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
    emit('done', f'Complete - {len(wordlist):,} words in {elapsed:.2f}s', 1.0)

    return {
        'count': len(wordlist),
        'elapsed': elapsed,
        'rate': int(len(wordlist) / elapsed),
        'file': abs_path,
        'sample_words': sample,
        'bases_count': len(bases),
        'roots_count': len(expanded),
        'aborted': aborted,
        'wordlist': wordlist,
    }

def _auto_filename() -> str:
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'cipherforge_{ts}.txt'

def _partial_result(wordlist: set, start: float, output_path, bases, roots: int, aborted: bool) -> dict:
    return {
        'count': 0,
        'elapsed': time.time() - start,
        'rate': 0,
        'file': output_path or '',
        'sample_words': [],
        'bases_count': len(bases),
        'roots_count': roots,
        'aborted': aborted,
        'wordlist': wordlist,
    }
