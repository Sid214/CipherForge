#!/usr/bin/env python3
"""
cipherforge.py
══════════════════════════════════════════════════════════════════
CipherForge — Adaptive Password Wordlist Studio
Single unified entry point: GUI launcher or CLI tool.

  GUI mode  (default when no profile args are passed):
    python cipherforge.py
    python cipherforge.py --gui

  CLI mode  (when profile args are provided):
    python cipherforge.py --name john --year 1990 [OPTIONS]

Usage:
    python cipherforge.py --help
══════════════════════════════════════════════════════════════════
"""
from __future__ import annotations
__version__ = "2.6.0"
__author__ = "Siddhesh"
AUTHOR = "Siddhesh"

import sys
import os
import argparse

# Ensure project root on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ── CLI argument parser ───────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="cipherforge",
        description="CipherForge — Adaptive Password Wordlist Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch the GUI studio (default when no profile args)
  python cipherforge.py

  # CLI: basic generation
  python cipherforge.py --name john --year 1990

  # CLI: full profile with analysis
  python cipherforge.py --name john --last khan --year 1990 --pet max --city london --analyze

  # CLI: estimate count only, no generation
  python cipherforge.py --name sarah --year 2001 --count

  # CLI: custom output file, tight length range
  python cipherforge.py --name alex --year 1985 --min 8 --max 14 --output alex_list.txt
"""
    )
    # Profile
    prof = p.add_argument_group("Profile (at least --name and --year are required in CLI mode)")
    prof.add_argument("--name",   type=str, metavar="FIRST",  help="First name")
    prof.add_argument("--last",   type=str, metavar="LAST",   help="Last name")
    prof.add_argument("--year",   type=str, metavar="YYYY",   help="Birth year (4 digits)")
    prof.add_argument("--pet",    type=str, metavar="PET",    help="Pet name")
    prof.add_argument("--city",   type=str, metavar="CITY",   help="City name")
    prof.add_argument("--color",  type=str, metavar="COLOR",  help="Favorite color")
    prof.add_argument("--sport",  type=str, metavar="SPORT",  help="Favorite sport")
    # Generation options
    gen = p.add_argument_group("Generation options")
    gen.add_argument("--min",      type=int, default=6,  metavar="N",   help="Min word length (default: 6)")
    gen.add_argument("--max",      type=int, default=20, metavar="N",   help="Max word length (default: 20)")
    gen.add_argument("--leet-max", type=int, default=80, metavar="N",   help="Max leet variants per root (default: 80)")
    gen.add_argument("--output",   type=str, metavar="FILE",            help="Custom output filename")
    # Mode flags
    mode = p.add_argument_group("Mode flags")
    mode.add_argument("--gui",     action="store_true", help="Force GUI mode (default when no profile args)")
    mode.add_argument("--count",   action="store_true", help="Print count estimate only, do not generate")
    mode.add_argument("--analyze", action="store_true", help="Print entropy analysis after generation")
    return p


# ── CLI runner ────────────────────────────────────────────────────────────────
def run_cli(args: argparse.Namespace) -> None:
    from cipherforge.core.generator import run_pipeline, estimate_count, build_base_candidates
    from cipherforge.core.analyzer  import analyze_wordlist

    profile = {
        "name":  args.name.strip().lower() if args.name else "",
        "last":  (args.last or "").strip().lower(),
        "year":  (args.year or "").strip(),
        "pet":   (args.pet or "").strip().lower(),
        "city":  (args.city or "").strip().lower(),
        "color": (args.color or "").strip().lower(),
        "sport": (args.sport or "").strip().lower(),
    }

    if not profile["name"]:
        print("[ERR] --name is required in CLI mode.", file=sys.stderr)
        sys.exit(1)
    if not profile["year"] or not profile["year"].isdigit() or len(profile["year"]) != 4:
        print("[ERR] --year must be exactly 4 digits (e.g. 1990).", file=sys.stderr)
        sys.exit(1)

    print()
    print("  CipherForge  |  Wordlist Synthesis Engine")
    print("  " + "-" * 42)

    if args.count:
        bases = build_base_candidates(profile)
        est   = estimate_count(profile, args.leet_max)
        print(f"  Seed roots      : {len(bases)}")
        print(f"  Est. candidates : ~{est:,}")
        print("  (Actual will be fewer after length filter + dedup)")
        print()
        return

    try:
        from tqdm import tqdm
        HAS_TQDM = True
    except ImportError:
        HAS_TQDM = False

    pbar = None
    last_pct = [0]

    def progress_cb(p: dict):
        pct = p.get("pct", 0)
        if HAS_TQDM and pbar:
            delta = int(pct * 100) - last_pct[0]
            if delta > 0:
                pbar.update(delta)
                last_pct[0] = int(pct * 100)

    if HAS_TQDM:
        pbar = tqdm(total=100, desc="CipherForge", unit="%", bar_format="{desc}: {percentage:3.0f}%|{bar}| {percentage:3.0f}%")

    result = run_pipeline(
        profile,
        progress_cb=progress_cb,
        leet_max=args.leet_max,
        min_len=args.min,
        max_len=args.max,
        output_path=args.output or None,
    )

    if HAS_TQDM and pbar:
        pbar.update(100 - last_pct[0])
        pbar.close()

    print()
    print(f"  [OK] Generated  {result['count']:>8,} words")
    print(f"  [T]  Elapsed    {result['elapsed']:.2f}s  ({result['rate']:,} words/sec)")
    if result.get("file"):
        print(f"  [S]  Saved to   {result['file']}")
    print()

    if args.analyze and result["count"] > 0:
        words = result.get("wordlist", set())
        if words:
            a = analyze_wordlist(words)
            print("  Entropy Analysis")
            print("  " + "-" * 36)
            print(f"  Avg entropy  : {a.avg_entropy:.3f} bits")
            print(f"  Max entropy  : {a.max_entropy:.3f} bits")
            print(f"  Min entropy  : {a.min_entropy:.3f} bits")
            print(f"  Avg length   : {a.avg_length:.1f} chars")
            print()
            print("  Strength tiers (sampled):")
            for tier, count in a.strength_tiers.items():
                bar = "#" * min(count // max(result["count"] // 50, 1), 20)
                print(f"    {tier:<10}: {count:>7,}  {bar}")
            print()
            print("  Top 10 highest-entropy words:")
            for score, word in sorted([(e, w) for w, e in a.entropy_scores], reverse=True)[:10]:
                print(f"    {score:.4f}  {word}")
            print()


# ── Entry point ───────────────────────────────────────────────────────────────
def main():
    parser = build_parser()

    # If no args at all -> launch GUI
    if len(sys.argv) == 1:
        _launch_gui()
        return

    args = parser.parse_args()

    # --gui flag or no profile data -> launch GUI
    if args.gui or not args.name:
        _launch_gui()
        return

    # Otherwise run CLI
    run_cli(args)


def _launch_gui():
    if sys.platform == "win32":
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("cipherforge.wordlist.studio.v2")
        except Exception:
            pass
    try:
        from cipherforge.gui import launch_gui
        launch_gui()
    except ImportError as e:
        print(f"[ERR] GUI dependencies missing: {e}", file=sys.stderr)
        print("      Install with:  pip install PyQt6", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
