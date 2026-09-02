#!/usr/bin/env python3
"""
wordgen.py — CipherForge CLI Entry Point

Usage examples:
  python wordgen.py --name john --year 1990 --pet max --city london
  python wordgen.py --name sarah --last khan --year 2001 --sport cricket --count
  python wordgen.py --name alex --year 1985 --pet rocky --min 8 --max 15 --analyze
  python wordgen.py --name john --year 1990 --leet-max 120 --output my_list.txt
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from cipherforge.core.generator import run_pipeline, estimate_count, build_base_candidates
from cipherforge.core.analyzer  import analyze_wordlist
from cipherforge.core.rules     import DEFAULT_MIN_LEN, DEFAULT_MAX_LEN, DEFAULT_LEET_MAX

try:
    from tqdm import tqdm as _tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False


def parse_args():
    p = argparse.ArgumentParser(
        prog="wordgen",
        description="CipherForge — Smart Password Wordlist Generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python wordgen.py --name john --year 1990 --pet max
  python wordgen.py --name sarah --year 2001 --count
  python wordgen.py --name alex --year 1985 --min 8 --max 15 --analyze
""",
    )
    p.add_argument("--name",      required=True,  help="First name")
    p.add_argument("--last",                      help="Last name")
    p.add_argument("--year",      required=True,  help="Birth year (4 digits)")
    p.add_argument("--pet",                       help="Pet name")
    p.add_argument("--city",                      help="City name")
    p.add_argument("--color",                     help="Favorite color")
    p.add_argument("--sport",                     help="Favorite sport")
    p.add_argument("--min",       type=int, default=DEFAULT_MIN_LEN, metavar="N",
                                              help=f"Minimum password length (default: {DEFAULT_MIN_LEN})")
    p.add_argument("--max",       type=int, default=DEFAULT_MAX_LEN, metavar="N",
                                              help=f"Maximum password length (default: {DEFAULT_MAX_LEN})")
    p.add_argument("--leet-max",  type=int, default=DEFAULT_LEET_MAX, metavar="N",
                                              help=f"Max leet variants per root (default: {DEFAULT_LEET_MAX})")
    p.add_argument("--output",                    help="Custom output filename")
    p.add_argument("--count",     action="store_true",
                                              help="Estimate count only; do not generate or save")
    p.add_argument("--analyze",   action="store_true",
                                              help="Print entropy analysis after generation")
    return p.parse_args()


def main():
    args = parse_args()

    if not args.year.isdigit() or len(args.year) != 4:
        print("Error: --year must be exactly 4 digits (e.g. 1990)")
        sys.exit(1)

    profile = {
        'name':  args.name,
        'last':  args.last or '',
        'year':  args.year,
        'pet':   args.pet   or '',
        'city':  args.city  or '',
        'color': args.color or '',
        'sport': args.sport or '',
    }

    # ── Count-only mode ───────────────────────────────────────────────────────
    if args.count:
        est   = estimate_count(profile, args.leet_max)
        bases = build_base_candidates(profile)
        print(f"\n  CipherForge Permutation Forecast")
        print(f"  ---------------------------------")
        print(f"  Seed combination roots : {len(bases):,}")
        print(f"  Estimated candidates   : ~{est:,}")
        print(f"  (Actual unique words will be fewer after dedup & length filter)\n")
        return

    # ── Full generation mode ──────────────────────────────────────────────────
    pbar = None
    if HAS_TQDM:
        pbar = _tqdm(total=100, desc="CipherForge", unit="%", bar_format="{l_bar}{bar}| {n:.0f}%")

    def progress_cb(p: dict):
        if pbar:
            pbar.n = int(p['pct'] * 100)
            pbar.set_postfix_str(p['detail'][:60])
            pbar.refresh()

    try:
        result = run_pipeline(
            profile,
            progress_cb=progress_cb,
            leet_max=getattr(args, 'leet_max', DEFAULT_LEET_MAX),
            min_len=args.min,
            max_len=args.max,
            output_path=args.output or None,
        )
    except KeyboardInterrupt:
        if pbar:
            pbar.close()
        print("\n[!] Interrupted - partial results may have been saved.")
        sys.exit(0)

    if pbar:
        pbar.n = 100
        pbar.refresh()
        pbar.close()

    print()
    if result['count'] == 0:
        print("  No words matched the length filter. Try widening --min / --max.")
    else:
        print(f"  [OK] Generated  {result['count']:,} words")
        print(f"  [T]  Elapsed    {result['elapsed']:.2f}s  ({result['rate']:,} words/sec)")
        if result.get('file'):
            print(f"  [S]  Saved to   {result['file']}")

        # ── Optional analysis ─────────────────────────────────────────────────
        if args.analyze and result.get('wordlist'):
            print()
            print("  Entropy Analysis")
            print("  ---------------------------------")
            analysis = analyze_wordlist(result['wordlist'])
            print(f"  Avg entropy  : {analysis.avg_entropy:.3f} bits")
            print(f"  Max entropy  : {analysis.max_entropy:.3f} bits")
            print(f"  Min entropy  : {analysis.min_entropy:.3f} bits")
            print(f"  Avg length   : {analysis.avg_length:.1f} chars")
            print()
            print("  Strength tiers (sampled):")
            for tier, count in analysis.strength_tiers.items():
                bar = "#" * min(count // max(analysis.total_words // 40, 1), 30)
                print(f"    {tier:10s}: {count:6,}  {bar}")
            print()
            print("  Top 10 highest-entropy words:")
            for word, entropy in analysis.entropy_scores[:10]:
                print(f"    {entropy:.4f}  {word}")
    print()


if __name__ == "__main__":
    main()
