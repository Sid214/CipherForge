<div align="center">

  <p align="center" style="margin: 0 0 18px 0;">
    <img src="cipherforge/assets/logo.png" width="68" height="68" align="middle" style="vertical-align: middle; margin-right: 16px;" alt="CipherForge Logo" /><strong style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; font-size: 32px; font-weight: 800; letter-spacing: 1.5px; vertical-align: middle;">CIPHERFORGE</strong>
  </p>

  <p align="center" style="margin: 0 0 10px 0;">
    <strong style="font-size: 21px; font-weight: 600;">Targeted Credential Permutation &amp; Entropy Analysis Suite</strong>
  </p>

  <p align="center" style="margin: 0 0 18px 0; max-width: 680px; font-size: 14px; line-height: 1.5;">
    A desktop application and scriptable CLI tool engineered for security auditors, penetration testers, and security researchers to benchmark credential resilience using targeted psychological anchor profiling.
  </p>

  <p align="center" style="margin: 0 0 18px 0;">
    <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10%2B-blue.svg" alt="Python" /></a>&nbsp;
    <a href="https://www.riverbankcomputing.com/software/pyqt/"><img src="https://img.shields.io/badge/GUI-PyQt6-green.svg" alt="GUI Framework" /></a>&nbsp;
    <img src="https://img.shields.io/badge/Engine-3--Stage%20Synthesis-orange.svg" alt="Engine" />&nbsp;
    <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-purple.svg" alt="License: MIT" /></a>&nbsp;
    <img src="https://img.shields.io/badge/Author-Siddhesh-brightgreen.svg" alt="Author" />
  </p>

</div>

---

## Executive Overview

Standard brute-force credential audits frequently rely on static public breach dumps or generic rainbow tables containing billions of irrelevant entries. However, real-world human-selected passwords overwhelmingly originate from personal semantic anchors: names of family members, significant dates, locations, pets, sports, and predictable character substitutions.

**CipherForge** models target-specific credential patterns. It generates compact, high-probability dictionaries through bounded combinatorial mutations, leetspeak transformations, and mathematical Shannon entropy evaluation without injecting generic dictionary filler.

---

## Key Highlights

- **Semantic Anchor Profiling**: Synthesizes permutations strictly derived from user-supplied parameters (Name, Last Name, Birth Year, Location, Pet, Favorite Sport, Favorite Color, Family Members, and Custom Passphrases).
- **Zero-Filler Architecture**: Generic credential words (such as `admin`, `root`, `user`, or `pass`) are never artificially injected as synthetic roots or prefixes unless explicitly supplied by the auditor.
- **Controlled Combinatorial Depth**: The Leet Depth matrix regulates mutation complexity (20 to 200 variants per root), preventing combinatorial explosion and memory exhaustion.
- **Mathematical Entropy Scoring**: Calculates character-level Shannon information entropy ($H = -\sum p(c) \log_2 p(c)$) and categorizes candidates into four resilience tiers: *Weak*, *Fair*, *Strong*, and *Excellent*.
- **Live Telemetry & Metrics**: Real-time visualization of word length distributions, character frequency distributions, and structural pattern compositions.
- **Sub-Millisecond Abort Handling**: Pipeline cancellation signals are checked every 20 to 100 iterations, immediately halting execution upon user request with zero partial disk writes.
- **Enterprise-Grade PyQt6 Interface**: Includes native Light and Dark modes (defaulting to Light Mode), a custom-styled telemetry terminal with aligned logging, dynamic downward-expanding dropdowns, touchpad-isolated slider controls, and full DPI scaling.
- **Unified Dual-Mode Engine**: Run as an interactive desktop suite (`cipherforge.py`) or headlessly within automated testing pipelines (`cipherforge.py --name ... --year ...`).

---

## System Architecture

```
                  ┌────────────────────────────────────────┐
                  │    Target Profile & Anchor Inputs      │
                  └───────────────────┬────────────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Stage 1: Seed Matrix      │
                        │ - Personal tokens         │
                        │ - Relational linkages     │
                        │ - Custom phrases          │
                        │ - Special separators      │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Stage 2: Case & Leet      │
                        │ - 5 case variations       │
                        │ - 10-char leet matrix     │
                        │ - Bounded permutations    │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                        ┌───────────────────────────┐
                        │ Stage 3: Affixes & Bounds │
                        │ - 22 suffix patterns      │
                        │ - Dynamic birth years     │
                        │ - Length bounds filtering │
                        │ - Hash set deduplication  │
                        └─────────────┬─────────────┘
                                      │
                                      ▼
                  ┌────────────────────────────────────────┐
                  │ Shannon Entropy & Quality Analytics    │
                  │ - Bit entropy calculation              │
                  │ - 4-tier resilience matrix             │
                  │ - Selective tier file export           │
                  └────────────────────────────────────────┘
```

---

## Technical Specifications

| Parameter | Specification | Description |
|---|---|---|
| **Python Core** | `Python >= 3.10` | Built with standard library concurrency and typed structures |
| **Desktop Framework** | `PyQt6 >= 6.6.0` | Hardware-accelerated desktop interface with custom Fusion styling |
| **Image Processing** | `Pillow >= 10.0.0` | Multi-resolution Windows application icon integration |
| **CLI Progress** | `tqdm >= 4.66.0` | Smooth command-line terminal progress indicators |
| **Default Length Window** | `6 to 20 characters` | Configurable from 1 to 128 characters |
| **Permutation Depth** | `20 to 200 roots` | Adjustable slider controlling maximum leetspeak substitutions |
| **Operating Systems** | `Windows / Linux / macOS` | Cross-platform compatibility with native Windows taskbar integration |

---

## Project Structure

```
CipherForge/
|-- cipherforge/
|   |-- assets/
|   |   |-- app_icon.ico          # Multi-resolution Windows application icon (16x16 to 256x256)
|   |   |-- chevron_down.png      # Custom combobox dropdown chevron
|   |   |-- logo.png              # Official brand logo (RGBA transparent)
|   |   `-- logo.jpg              # Brand asset fallback
|   |-- core/
|   |   |-- __init__.py           # Core module exports
|   |   |-- analyzer.py           # Shannon entropy engine and structural analysis
|   |   |-- generator.py          # 3-stage combinatorial generation engine
|   |   `-- rules.py              # Substitution mappings, suffixes, and constraints
|   |-- gui/
|   |   |-- __init__.py           # GUI package exports
|   |   `-- app_qt.py             # PyQt6 desktop suite and event controllers
|   `-- __init__.py               # Package metadata and author attribution
|-- generated_wordlists/          # Standard storage directory for generated dictionaries
|-- cipherforge.py                # Single unified entrypoint (GUI launcher or CLI engine)
|-- requirements.txt              # Production dependency specifications
|-- LICENSE                       # Official MIT License
`-- README.md                     # Comprehensive technical documentation
```

---

## Installation & Setup

### 1. Prerequisites
Ensure Python 3.10 or newer is installed on your workstation.

### 2. Clone the Repository
```bash
git clone https://github.com/your-org/CipherForge.git
cd CipherForge
```

### 3. Initialize Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scriptsctivate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Usage Guide

### Mode 1: Graphical Desktop Suite (Default)

Launch the interactive suite:
```bash
python cipherforge.py
```
*(Passing no arguments or passing `--gui` opens the desktop suite.)*

#### Desktop Workflow:
1. **Target Parameters**: Enter known profile anchors (Name, Last Name, Birth Year, Location, Pet, Color, Sport).
2. **Family Relations**: Select relational roles from the dropdown (`Spouse`, `Child`, `Sibling`, `Parent`, `Close Friend`, `Other`) and click `+ Add Member` to build compound semantic links.
3. **Custom Keywords**: Input known phrases, past passwords, or enterprise naming conventions (comma-separated).
4. **Synthesis Boundaries**: Set length boundaries (e.g., `8` to `16`) and configure the Leet Depth slider.
5. **Generation**: Click `⚡ Generate Wordlist`. Progress updates stream into the live telemetry terminal, and the output is saved to `generated_wordlists/`.
6. **Analytics & Entropy**: Navigate to *Wordlist Analytics* to review character and length distributions, or open *Entropy Inspector* to test individual passwords and export filtered strength tiers.

---

### Mode 2: Command-Line Interface (CLI)

Run automated, headless wordlist generation in security pipelines:

```bash
# Basic profile generation
python cipherforge.py --name Aarav --year 1995 --pet Bruno

# Comprehensive profile with length boundaries and custom output path
python cipherforge.py --name Aarav --last Sharma --year 1995 --city Mumbai --min 8 --max 16 --leet-max 100 --output enterprise_audit.txt

# Generation with full post-run Shannon entropy breakdown
python cipherforge.py --name Aarav --year 1995 --pet Bruno --analyze

# Fast forecast: Estimate candidate count without writing to disk
python cipherforge.py --name Aarav --year 1995 --count
```

#### CLI Command-Line Reference:

| Flag | Argument | Description |
|---|---|---|
| `--gui` | *None* | Launch the graphical desktop suite |
| `--name` | `TEXT` | Target first name (primary anchor) |
| `--last` | `TEXT` | Target last name / surname |
| `--year` | `YYYY` | Target 4-digit birth year |
| `--pet` | `TEXT` | Target pet name |
| `--city` | `TEXT` | Target location or city |
| `--color` | `TEXT` | Target favorite color |
| `--sport` | `TEXT` | Target favorite sport |
| `--min` | `INT` | Minimum password length (default: 6) |
| `--max` | `INT` | Maximum password length (default: 20) |
| `--leet-max`, `--leet` | `INT` | Maximum leet substitutions per root (default: 80) |
| `--output` | `FILE` | Custom output filepath (.txt) |
| `--count` | *None* | Print candidate estimate and exit without writing |
| `--analyze` | *None* | Print post-generation Shannon entropy analysis |

---

## Mathematical Entropy Rating Model

CipherForge quantifies information density using Shannon's Information Entropy formula:

$$H = -\sum_{i=1}^{n} p(c_i) \log_2 p(c_i) \quad [\text{bits/character}]$$

Where $p(c_i)$ represents the probability of character $c_i$ appearing within the candidate string of length $n$.

### Resilience Tiers:

- **Weak (< 2.0 bits)**: High character redundancy, repetitive patterns, or short character sets.
- **Fair (2.0 – 3.0 bits)**: Standard lowercase alphanumeric sequences with moderate diversity.
- **Strong (3.0 – 3.8 bits)**: High-complexity combinations featuring mixed casing, digits, and symbols.
- **Excellent (> 3.8 bits)**: Dense, high-entropy character permutations offering high mathematical unpredictability.

---

## Quality Audit & Engineering Changelog

- **Wordlist Generation Source Correction**: Removed all legacy hardcoded prefixes (`admin_`, `user_`, `root_`, `hack_`, `pass_`, `secret_`) from core generation rules. Candidates are derived strictly from user-provided inputs.
- **Engine Guide Redesign**: Overhauled the documentation interface with enhanced typography, balanced two-column technical breakdowns, accurate algorithmic descriptions, and operational auditing guidance.
- **Sub-Millisecond Pipeline Abort**: Implemented responsive cancellation checks across Stage 2 and Stage 3 loops, ensuring immediate worker termination with zero file output upon cancellation.
- **Touchpad Scroll Isolation**: Implemented `ScrollIgnoringSlider` to route two-finger touchpad gestures directly to the parent scroll area, preventing accidental adjustments to the Leet Depth slider.
- **Dropdown Architecture**: Eliminated duplicate rectangular containers and sharp corners; implemented dynamic positioning so the popup menu originates strictly beneath the field with exact edge and width alignment.
- **Telemetry Console Polish**: Initialized the terminal with a standby status indicator (`> Ready — CipherForge telemetry initialized.`), added internal padding, and formatted sub-detail logs with an 11-space indent matching the timestamp width.
- **Thread Safety & Lifecycle**: Implemented `closeEvent` thread cleanup to prevent thread destruction errors on application exit.
- **Official Windows App Icon**: Embedded multi-resolution `.ico` assets and registered an explicit Windows `AppUserModelID` (`cipherforge.wordlist.studio.v2`) for taskbar identification.
- **Dependency & Code Cleanup**: Removed legacy `customtkinter` references, purged orphaned `.pyc` caches, and cleaned unused imports.

---

## Ethical Use & Legal Disclaimer

CipherForge is designed exclusively for authorized penetration testing, security compliance evaluations, personal account recovery, and academic research. 

Unauthorized access to computer systems, networks, or digital assets without prior explicit written authorization from the asset owner is strictly illegal. The author and contributors accept no liability for misuse, damages, or illegal actions committed with this software.

---

## Author & Attribution

**Engineered with care • Siddhesh**  
*CipherForge Studio v2.6.0*

---

## License

Distributed under the **MIT License**. See [LICENSE](LICENSE) for full legal text.
