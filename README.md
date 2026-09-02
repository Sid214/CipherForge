# ⚡ CipherForge

> **Adaptive Password Wordlist Engine** — A high-performance Python tool for generating
> smart, entropy-aware wordlists from personal profile data. Available as both a
> modern GUI application and a powerful CLI tool.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔑 **Smart Generation** | 3-stage pipeline: seed → expand → affixes |
| 🔤 **Leet Substitutions** | Bounded itertools.product (no exponential freeze) |
| 🔡 **Case Variations** | lowercase, UPPERCASE, Capitalized, aLtErNaTiNg |
| 🏷️ **Affix Combos** | 7 prefixes × 22 suffixes applied to every root |
| 📊 **Statistics Tab** | Length distribution, char frequency, pattern breakdown |
| 🔐 **Entropy Analyzer** | Shannon entropy ranking, tier filter, strong-only export |
| 🎨 **Light/Dark/Auto** | Full appearance mode switching in GUI |
| ⚡ **Zero-Freeze UI** | Background thread + queue polling — UI always responsive |
| 💾 **Auto-Named Output** | `cipherforge_YYYYMMDD_HHMMSS.txt` if no name given |

---

## 📁 Project Structure

```
wordlist/
├── cipherforge/                    # Core package
│   ├── core/
│   │   ├── rules.py                # Leet map, prefixes, suffixes constants
│   │   ├── generator.py            # 3-stage high-speed permutation engine
│   │   └── analyzer.py             # Entropy & statistics analysis
│   ├── gui/
│   │   ├── app.py                  # Unified zero-lag responsive studio GUI
│   │   └── __init__.py             # GUI package exports
│   ├── assets/
│   │   └── logo.jpg                # CipherForge cyberpunk logo
│   └── __init__.py                 # Package versioning
├── wordgen.py                      # CLI entry point (terminal use)
├── wordgen_gui.py                  # GUI entry point (desktop launch)
├── requirements.txt                # Dependencies (customtkinter, tqdm, Pillow)
└── README.md                       # Documentation
```

---

## 🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Launch the GUI

```bash
python wordgen_gui.py
```

### 3. Or use the CLI

```bash
python wordgen.py --name john --year 1990 --pet max --city london
```

---

## 🖥️ GUI Walkthrough

### ⚡ Generator Engine Tab

Fill in the target profile — only **First Name** and **Birth Year** are required.
All other fields enrich the combination matrix.

| Field | Example | Effect |
|---|---|---|
| First Name * | `john` | Primary anchor for all combos |
| Last Name | `khan` | Adds name+last, last+name combos |
| Birth Year * | `1990` | Appended to all roots |
| Pet Name | `max` | name+pet, pet+year, name+pet+year |
| City | `london` | name+city+year combos |
| Favorite Color | `blue` | Extra enricher tokens |
| Favorite Sport | `cricket` | Extra enricher tokens |

**Options:**
- **Min/Max Length** — filter generated words by character count
- **Leet Depth** — slider to control leet substitution breadth (20–200)
- **Output File** — custom filename, or auto-generates `cipherforge_TIMESTAMP.txt`

**Buttons:**
- **⚡ Generate Wordlist** — starts the full 3-stage pipeline
- **🔢 Estimate Count** — fast forecast without generating
- **⛔ Stop** — gracefully cancels mid-run
- **📂 Open Folder** — opens the output directory in Explorer

After generation, the **Statistics** and **Entropy Analyzer** tabs auto-populate.

---

### 📊 Statistics Tab

Automatically populated after a generation run. Shows:

- **KPI Row** — Total Words, Avg Length, Avg/Max Entropy, Strong+ Words count
- **Length Distribution** — Horizontal bar chart of word lengths
- **Character Frequency** — Top 20 most-used characters
- **Pattern Breakdown** — Donut chart: prefix%, leet%, suffix%, uppercase%
- **Strength Tiers** — Bar chart of Weak/Fair/Strong/Excellent counts

---

### 🔐 Entropy Analyzer Tab

Displays the full Shannon entropy ranking of generated words (up to 5,000 sampled).

**Tier Legend:**

| Tier | Entropy Range | Color |
|---|---|---|
| Weak | < 2.0 bits | 🔴 Red |
| Fair | 2.0 – 3.0 bits | 🟡 Amber |
| Strong | 3.0 – 3.8 bits | 🟢 Green |
| Excellent | > 3.8 bits | 🔵 Violet |

**Controls:**
- **Filter** — Show only Weak / Fair / Strong / Excellent words
- **💾 Export Filtered** — Save the currently visible tier to a new `.txt` file

---

## 💻 CLI Reference

```bash
python wordgen.py [OPTIONS]
```

### Required

| Flag | Description |
|---|---|
| `--name NAME` | First name |
| `--year YEAR` | Birth year (exactly 4 digits) |

### Optional Profile Enrichers

| Flag | Description |
|---|---|
| `--last LAST` | Last name |
| `--pet PET` | Pet name |
| `--city CITY` | City name |
| `--color COLOR` | Favorite color |
| `--sport SPORT` | Favorite sport |

### Generation Controls

| Flag | Default | Description |
|---|---|---|
| `--min N` | `6` | Minimum word length |
| `--max N` | `20` | Maximum word length |
| `--leet-max N` | `80` | Max leet permutations per root |
| `--output FILE` | auto | Custom output filename |

### Informational

| Flag | Description |
|---|---|
| `--count` | Print estimated count only — do not generate |
| `--analyze` | Print entropy analysis after generation |

### Examples

```bash
# Basic run — name + year only
python wordgen.py --name john --year 1990

# Full profile
python wordgen.py --name john --last khan --year 1990 --pet max --city london --color blue

# Just see the estimate, don't generate
python wordgen.py --name sarah --last khan --year 2001 --sport cricket --count

# 8–15 character words only, with entropy analysis
python wordgen.py --name alex --year 1985 --pet rocky --min 8 --max 15 --analyze

# Custom output filename, high leet depth
python wordgen.py --name mike --year 1995 --leet-max 150 --output mike_list.txt
```

---

## ⚙️ Generation Algorithm

```
Profile Tokens
      │
      ▼
Stage 1: build_base_candidates()
  • Single tokens: name, last, pet, city, color, sport
  • Pairings: name+year, name+pet, pet+year, name+last, name+city
  • Triples: name+pet+year, name+city+year, name+last+year
  • Special-separated: name+!+year, name+@+year, ... (9 specials)
  • All concatenated: name+last+pet+city+color+sport+year
      │
      ▼  (~30–60 seeds for a full profile)
Stage 2: expand_variants()
  • 5 case modes per root (lower, UPPER, Capital, aLt, ALt)
  • Up to leet_max leet permutations via itertools.islice
      │
      ▼  (~1,000–5,000 expanded roots)
Stage 3: apply_affixes()
  • 7 PREFIXES × 22+ SUFFIXES = 154+ combinations per root
  • Length filter applied: [min_len, max_len]
  • Deduplicated via Python set
      │
      ▼  (20,000–150,000 unique words, generated in <0.5s)
     Output: sorted .txt file
```

---

## 🔧 Extending CipherForge

All rules live in [`cipherforge/core/rules.py`](cipherforge/core/rules.py):

```python
# Add a new leet substitution
LEET_MAP['c'] = ['(', '<']

# Add new prefixes
PREFIXES.append("sys_")

# Add new suffixes
SUFFIXES.extend(["2023", "xyz", "!!"])
```

No other files need modification.

---

## 📦 Dependencies

| Package | Version | Purpose |
|---|---|---|
| `customtkinter` | ≥ 6.0.0 | Modern GUI framework |
| `tqdm` | ≥ 4.70.0 | CLI progress bar |
| `Pillow` | ≥ 10.0.0 | Logo image display in GUI |

Install all: `pip install -r requirements.txt`

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*CipherForge v2.5.0 — Built with Python + CustomTkinter*
