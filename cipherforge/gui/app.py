"""
cipherforge/gui/app.py
───────────────────────
CipherForge — Modern, High-Performance Wordlist Studio GUI.
Engineered with CustomTkinter for sleek aesthetics, zero-lag responsive design,
symmetrical layouts, seamless Light/Dark mode switching, and 100% working features.
"""

from __future__ import annotations

import os
import sys
import queue
import threading
import datetime
import subprocess
import customtkinter as ctk

from ..core.generator import run_pipeline, estimate_count, build_base_candidates
from ..core.analyzer import analyze_wordlist, shannon_entropy, strength_tier
from ..core.rules import DEFAULT_MIN_LEN, DEFAULT_MAX_LEN, DEFAULT_LEET_MAX

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# ── Universal Light / Dark Theme Palette ──────────────────────────────────────
C_BG_APP         = ("#F8FAFC", "#090D16")  # App background
C_BG_SIDEBAR     = ("#FFFFFF", "#0F1626")  # Sidebar background
C_BG_CARD        = ("#FFFFFF", "#131C2E")  # Card container
C_BG_SUB_CARD    = ("#F1F5F9", "#0B111E")  # Nested cards / badges
C_BORDER         = ("#E2E8F0", "#1C2840")  # Card borders
C_INPUT_BG       = ("#F8FAFC", "#0B111E")  # Form input fields
C_INPUT_BORDER   = ("#CBD5E1", "#223250")  # Form input borders
C_TEXT_MAIN      = ("#0F172A", "#F8FAFC")  # Primary text
C_TEXT_MUTED     = ("#64748B", "#94A3B8")  # Secondary / sub text
C_CONSOLE_BG     = ("#F8FAFC", "#060A12")  # Telemetry console
C_CONSOLE_TXT    = ("#0284C7", "#38BDF8")  # Telemetry text

C_ACCENT         = "#2563EB"               # Electric Blue primary
C_ACCENT_HOVER   = "#1D4ED8"               # Hover state
C_SUCCESS        = "#10B981"               # Emerald Green
C_WARN           = "#F59E0B"               # Amber Warning
C_ERR            = "#EF4444"               # Crimson Error
C_PURPLE         = "#8B5CF6"               # Royal Purple

ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")


class CipherForgeApp(ctk.CTk):
    """Main Application Window with Sidebar Navigation & Zero-Lag View Switching."""

    def __init__(self):
        super().__init__()

        # Appearance defaults
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("CipherForge — Adaptive Password Wordlist Studio")
        self.geometry("1160x780")
        self.minsize(920, 640)
        self.configure(fg_color=C_BG_APP)

        # Internal state
        self._stop_event    = threading.Event()
        self._log_queue     = queue.Queue()
        self._is_generating = False
        self._last_result   = None
        self._last_analysis = None
        self._last_file     = None

        # Root Grid: Col 0 = Sidebar (fixed width), Col 1 = Main Viewport
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_viewport()

        # Switch to default view
        self._navigate_to("generator")

        # Start non-blocking UI queue listener
        self._poll_worker_queue()

    # ── Sidebar Navigation ────────────────────────────────────────────────────
    def _build_sidebar(self):
        self._sidebar = ctk.CTkFrame(
            self, width=240, corner_radius=0,
            fg_color=C_BG_SIDEBAR, border_color=C_BORDER, border_width=1
        )
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        self._sidebar.grid_propagate(False)
        self._sidebar.grid_rowconfigure(8, weight=1)

        # Brand header
        brand_box = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        brand_box.grid(row=0, column=0, padx=16, pady=(20, 10), sticky="ew")

        logo_path = os.path.join(ASSETS_DIR, "logo.jpg")
        if HAS_PIL and os.path.exists(logo_path):
            try:
                raw_img = Image.open(logo_path).resize((48, 48), Image.LANCZOS)
                self._logo_ctk = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(48, 48))
                ctk.CTkLabel(brand_box, image=self._logo_ctk, text="").pack(side="left", padx=(0, 10))
            except Exception:
                ctk.CTkLabel(brand_box, text="⚡", font=ctk.CTkFont(size=32), text_color=C_ACCENT).pack(side="left", padx=(0, 10))
        else:
            ctk.CTkLabel(brand_box, text="⚡", font=ctk.CTkFont(size=32), text_color=C_ACCENT).pack(side="left", padx=(0, 10))

        title_col = ctk.CTkFrame(brand_box, fg_color="transparent")
        title_col.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            title_col, text="CipherForge",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=C_TEXT_MAIN
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_col, text="Wordlist Studio v2.5",
            font=ctk.CTkFont(size=10), text_color=C_TEXT_MUTED
        ).pack(anchor="w")

        # Divider
        ctk.CTkFrame(self._sidebar, height=1, fg_color=C_BORDER).grid(row=1, column=0, padx=16, pady=8, sticky="ew")

        # Nav Buttons
        self._nav_items = [
            ("generator", "⚡", "Generator Engine"),
            ("statistics", "📊", "Wordlist Statistics"),
            ("entropy", "🔐", "Entropy Inspector"),
            ("guide", "ℹ️", "User Guide & Rules"),
        ]
        self._nav_buttons: dict[str, ctk.CTkButton] = {}

        for idx, (view_id, icon, label) in enumerate(self._nav_items, start=2):
            btn = ctk.CTkButton(
                self._sidebar,
                text=f"  {icon}  {label}", anchor="w",
                height=38, corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="transparent",
                hover_color=("#E2E8F0", "#1C2840"),
                text_color=C_TEXT_MAIN,
                command=lambda v=view_id: self._navigate_to(v)
            )
            btn.grid(row=idx, column=0, padx=12, pady=3, sticky="ew")
            self._nav_buttons[view_id] = btn

        # Divider
        ctk.CTkFrame(self._sidebar, height=1, fg_color=C_BORDER).grid(row=6, column=0, padx=16, pady=12, sticky="ew")

        # Theme Switcher Box
        theme_card = ctk.CTkFrame(self._sidebar, fg_color=C_BG_SUB_CARD, corner_radius=10, border_color=C_BORDER, border_width=1)
        theme_card.grid(row=7, column=0, padx=12, pady=4, sticky="ew")
        ctk.CTkLabel(
            theme_card, text="🎨  Theme Mode",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=C_TEXT_MAIN
        ).pack(pady=(8, 4))

        self._theme_toggle = ctk.CTkSegmentedButton(
            theme_card, values=["🌙 Dark", "☀️ Light", "💻 Auto"],
            height=28, corner_radius=6,
            font=ctk.CTkFont(size=11),
            selected_color=C_ACCENT, selected_hover_color=C_ACCENT_HOVER,
            command=self._on_theme_switch
        )
        self._theme_toggle.set("🌙 Dark")
        self._theme_toggle.pack(padx=8, pady=(0, 8), fill="x")

        # Sidebar Footer: Real-time Status Badge
        foot_box = ctk.CTkFrame(self._sidebar, fg_color="transparent")
        foot_box.grid(row=9, column=0, padx=16, pady=16, sticky="sw")
        self._side_status_lbl = ctk.CTkLabel(
            foot_box, text="● Engine Ready",
            font=ctk.CTkFont(size=11, weight="bold"), text_color=C_SUCCESS
        )
        self._side_status_lbl.pack(anchor="w")
        self._side_words_lbl = ctk.CTkLabel(
            foot_box, text="0 words generated",
            font=ctk.CTkFont(size=10), text_color=C_TEXT_MUTED
        )
        self._side_words_lbl.pack(anchor="w")

    def _on_theme_switch(self, choice: str):
        if "Dark" in choice:
            ctk.set_appearance_mode("dark")
        elif "Light" in choice:
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("system")

    # ── Main Viewport Controller ──────────────────────────────────────────────
    def _build_viewport(self):
        self._viewport = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self._viewport.grid(row=0, column=1, sticky="nsew")
        self._viewport.grid_columnconfigure(0, weight=1)
        self._viewport.grid_rowconfigure(1, weight=1)

        # Header Bar with Current View Title + Quick Actions
        self._header = ctk.CTkFrame(
            self._viewport, height=54, corner_radius=0,
            fg_color=C_BG_SIDEBAR, border_color=C_BORDER, border_width=1
        )
        self._header.grid(row=0, column=0, sticky="ew")
        self._header.grid_propagate(False)
        self._header.grid_columnconfigure(0, weight=1)

        self._hdr_title = ctk.CTkLabel(
            self._header, text="Generator Engine",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=C_TEXT_MAIN
        )
        self._hdr_title.grid(row=0, column=0, padx=20, sticky="w")

        # Quick Actions in Header
        hdr_actions = ctk.CTkFrame(self._header, fg_color="transparent")
        hdr_actions.grid(row=0, column=1, padx=16, sticky="e")

        ctk.CTkButton(
            hdr_actions, text="✨ Fill Demo", width=95, height=28,
            corner_radius=6, font=ctk.CTkFont(size=11, weight="bold"),
            fg_color=C_BG_SUB_CARD, hover_color=C_BORDER, text_color=C_ACCENT,
            command=self._action_fill_demo
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            hdr_actions, text="📂 Open Folder", width=105, height=28,
            corner_radius=6, font=ctk.CTkFont(size=11),
            fg_color="transparent", hover_color=C_BORDER, text_color=C_TEXT_MUTED,
            border_color=C_BORDER, border_width=1,
            command=self._action_open_folder
        ).pack(side="left", padx=4)

        # View Containers (Swapped dynamically without duplicate tab headers)
        self._view_generator  = self._build_view_generator()
        self._view_statistics = self._build_view_statistics()
        self._view_entropy    = self._build_view_entropy()
        self._view_guide      = self._build_view_guide()

    def _navigate_to(self, view_id: str):
        # Update Nav button highlight
        for k, btn in self._nav_buttons.items():
            is_active = (k == view_id)
            btn.configure(
                fg_color=C_ACCENT if is_active else "transparent",
                hover_color=C_ACCENT_HOVER if is_active else ("#E2E8F0", "#1C2840"),
                text_color="#FFFFFF" if is_active else C_TEXT_MAIN
            )

        # Map Titles
        titles = {
            "generator": "⚡  Wordlist Generator Engine",
            "statistics": "📊  Wordlist Analytics & Distributions",
            "entropy": "🔐  Entropy Inspector & Security Analysis",
            "guide": "ℹ️  Engine Rules & User Guide",
        }
        self._hdr_title.configure(text=titles.get(view_id, "CipherForge"))

        # Hide all, reveal active
        self._view_generator.grid_remove()
        self._view_statistics.grid_remove()
        self._view_entropy.grid_remove()
        self._view_guide.grid_remove()

        if view_id == "generator":
            self._view_generator.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        elif view_id == "statistics":
            self._view_statistics.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        elif view_id == "entropy":
            self._view_entropy.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        elif view_id == "guide":
            self._view_guide.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)

    # ══════════════════════════════════════════════════════════════════════════
    # VIEW 1: GENERATOR ENGINE
    # ══════════════════════════════════════════════════════════════════════════
    def _build_view_generator(self) -> ctk.CTkScrollableFrame:
        container = ctk.CTkScrollableFrame(self._viewport, fg_color="transparent", corner_radius=0)
        container.grid_columnconfigure((0, 1), weight=1)

        # ── Card 1: Target Profile (Balanced 2-Column Grid) ────────────────────
        p_card = self._create_card(container, "👤  Target Profile Information", row=0, col=0, colspan=2)
        p_card.grid_columnconfigure((0, 1), weight=1)

        self._inputs: dict[str, ctk.CTkEntry] = {}

        fields_left = [
            ("First Name *", "name", "e.g. john"),
            ("Birth Year * (4 digits)", "year", "e.g. 1990"),
            ("City Name", "city", "e.g. london"),
            ("Favorite Sport", "sport", "e.g. cricket"),
        ]
        fields_right = [
            ("Last Name", "last", "e.g. khan"),
            ("Pet Name", "pet", "e.g. max"),
            ("Favorite Color", "color", "e.g. blue"),
            ("Custom Output File", "output", "auto-generated if empty"),
        ]

        for r_idx, (label, key, placeholder) in enumerate(fields_left):
            f = ctk.CTkFrame(p_card, fg_color="transparent")
            f.grid(row=r_idx, column=0, padx=(10, 6), pady=5, sticky="ew")
            f.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=C_TEXT_MAIN).grid(row=0, column=0, sticky="w")
            e = ctk.CTkEntry(f, placeholder_text=placeholder, height=36, corner_radius=6,
                             fg_color=C_INPUT_BG, border_color=C_INPUT_BORDER, text_color=C_TEXT_MAIN,
                             placeholder_text_color=C_TEXT_MUTED)
            e.grid(row=1, column=0, sticky="ew", pady=(2, 0))
            self._inputs[key] = e

        for r_idx, (label, key, placeholder) in enumerate(fields_right):
            f = ctk.CTkFrame(p_card, fg_color="transparent")
            f.grid(row=r_idx, column=1, padx=(6, 10), pady=5, sticky="ew")
            f.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(f, text=label, font=ctk.CTkFont(size=12, weight="bold"), text_color=C_TEXT_MAIN).grid(row=0, column=0, sticky="w")
            e = ctk.CTkEntry(f, placeholder_text=placeholder, height=36, corner_radius=6,
                             fg_color=C_INPUT_BG, border_color=C_INPUT_BORDER, text_color=C_TEXT_MAIN,
                             placeholder_text_color=C_TEXT_MUTED)
            e.grid(row=1, column=0, sticky="ew", pady=(2, 0))
            self._inputs[key] = e

        # ── Card 2: Filter Parameters ─────────────────────────────────────────
        f_card = self._create_card(container, "⚙️  Synthesis Boundaries", row=1, col=0, colspan=2)
        f_card.grid_columnconfigure((0, 1, 2), weight=1)

        # Min Length
        f_min = ctk.CTkFrame(f_card, fg_color="transparent")
        f_min.grid(row=0, column=0, padx=8, pady=4, sticky="ew")
        f_min.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_min, text="Min Length", font=ctk.CTkFont(size=12, weight="bold"), text_color=C_TEXT_MAIN).grid(row=0, column=0, sticky="w")
        self._inputs['min_len'] = ctk.CTkEntry(f_min, height=34, corner_radius=6, fg_color=C_INPUT_BG, border_color=C_INPUT_BORDER, text_color=C_TEXT_MAIN)
        self._inputs['min_len'].insert(0, "6")
        self._inputs['min_len'].grid(row=1, column=0, sticky="ew", pady=(2, 0))

        # Max Length
        f_max = ctk.CTkFrame(f_card, fg_color="transparent")
        f_max.grid(row=0, column=1, padx=8, pady=4, sticky="ew")
        f_max.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_max, text="Max Length", font=ctk.CTkFont(size=12, weight="bold"), text_color=C_TEXT_MAIN).grid(row=0, column=0, sticky="w")
        self._inputs['max_len'] = ctk.CTkEntry(f_max, height=34, corner_radius=6, fg_color=C_INPUT_BG, border_color=C_INPUT_BORDER, text_color=C_TEXT_MAIN)
        self._inputs['max_len'].insert(0, "20")
        self._inputs['max_len'].grid(row=1, column=0, sticky="ew", pady=(2, 0))

        # Leet Permutation Depth Slider
        f_leet = ctk.CTkFrame(f_card, fg_color="transparent")
        f_leet.grid(row=0, column=2, padx=8, pady=4, sticky="ew")
        f_leet.grid_columnconfigure(0, weight=1)
        self._leet_val_lbl = ctk.StringVar(value="Leet Depth: 80 variants/root")
        ctk.CTkLabel(f_leet, textvariable=self._leet_val_lbl, font=ctk.CTkFont(size=12, weight="bold"), text_color=C_TEXT_MAIN).grid(row=0, column=0, sticky="w")
        self._leet_slider = ctk.CTkSlider(
            f_leet, from_=20, to=200, number_of_steps=18,
            progress_color=C_ACCENT, button_color=C_ACCENT,
            command=lambda v: self._leet_val_lbl.set(f"Leet Depth: {int(v)} variants/root")
        )
        self._leet_slider.set(80)
        self._leet_slider.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        # ── Card 3: Execution Control & Progress ──────────────────────────────
        a_card = self._create_card(container, "🚀  Execution Control", row=2, col=0, colspan=2)
        a_card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._btn_generate = ctk.CTkButton(
            a_card, text="⚡  Generate Wordlist",
            font=ctk.CTkFont(size=13, weight="bold"), height=42, corner_radius=8,
            fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            command=self._action_start_generation
        )
        self._btn_generate.grid(row=0, column=0, columnspan=2, padx=8, pady=6, sticky="ew")

        self._btn_estimate = ctk.CTkButton(
            a_card, text="🔢  Estimate Count",
            font=ctk.CTkFont(size=12, weight="bold"), height=42, corner_radius=8,
            fg_color=C_BG_SUB_CARD, hover_color=C_BORDER, text_color=C_ACCENT,
            command=self._action_estimate_count
        )
        self._btn_estimate.grid(row=0, column=2, padx=8, pady=6, sticky="ew")

        self._btn_stop = ctk.CTkButton(
            a_card, text="⛔  Stop",
            font=ctk.CTkFont(size=12, weight="bold"), height=42, corner_radius=8,
            fg_color=("#FEE2E2", "#2A1215"), hover_color=C_ERR, text_color=C_ERR,
            state="disabled", command=self._action_stop_generation
        )
        self._btn_stop.grid(row=0, column=3, padx=8, pady=6, sticky="ew")

        # Progress Bar & Live Status
        p_row = ctk.CTkFrame(a_card, fg_color="transparent")
        p_row.grid(row=1, column=0, columnspan=4, padx=8, pady=(4, 2), sticky="ew")
        p_row.grid_columnconfigure(0, weight=1)

        self._progress_bar = ctk.CTkProgressBar(
            p_row, height=10, corner_radius=5,
            progress_color=C_ACCENT, fg_color=("#E2E8F0", "#1C2840")
        )
        self._progress_bar.set(0)
        self._progress_bar.grid(row=0, column=0, sticky="ew", pady=(2, 4))

        p_info = ctk.CTkFrame(p_row, fg_color="transparent")
        p_info.grid(row=1, column=0, sticky="ew")
        p_info.grid_columnconfigure(1, weight=1)

        self._lbl_status = ctk.CTkLabel(
            p_info, text="Ready to generate",
            font=ctk.CTkFont(size=11), text_color=C_TEXT_MUTED
        )
        self._lbl_status.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            p_info, text="Clear Log", width=70, height=22, corner_radius=4,
            font=ctk.CTkFont(size=10), fg_color="transparent", hover_color=C_BORDER,
            text_color=C_TEXT_MUTED, command=self._action_clear_console
        ).grid(row=0, column=1, sticky="e")

        # ── Card 4: Telemetry Log & KPI Metrics ────────────────────────────────
        log_card = self._create_card(container, "📋  Telemetry & Stream Log", row=3, col=0, colspan=2)
        log_card.grid_columnconfigure(0, weight=1)

        self._console = ctk.CTkTextbox(
            log_card, height=180, corner_radius=8,
            fg_color=C_CONSOLE_BG, text_color=C_CONSOLE_TXT,
            font=ctk.CTkFont(family="Cascadia Code, Consolas, Courier New", size=11),
            border_color=C_BORDER, border_width=1, state="disabled"
        )
        self._console.grid(row=0, column=0, padx=8, pady=(0, 8), sticky="nsew")

        # KPI Badges
        kpi_bar = ctk.CTkFrame(log_card, fg_color=C_BG_SUB_CARD, corner_radius=8, border_color=C_BORDER, border_width=1)
        kpi_bar.grid(row=1, column=0, padx=8, pady=(0, 4), sticky="ew")
        kpi_bar.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._kpi_words = self._create_kpi_cell(kpi_bar, "WORDS GENERATED", "0", 0, C_ACCENT)
        self._kpi_time  = self._create_kpi_cell(kpi_bar, "ELAPSED TIME", "0.00s", 1, C_SUCCESS)
        self._kpi_speed = self._create_kpi_cell(kpi_bar, "SYNTHESIS RATE", "0/s", 2, C_PURPLE)
        self._kpi_file  = self._create_kpi_cell(kpi_bar, "ARTIFACT PATH", "—", 3, C_WARN)

        return container

    # ══════════════════════════════════════════════════════════════════════════
    # VIEW 2: STATISTICS & ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    def _build_view_statistics(self) -> ctk.CTkScrollableFrame:
        container = ctk.CTkScrollableFrame(self._viewport, fg_color="transparent", corner_radius=0)
        container.grid_columnconfigure((0, 1), weight=1)

        # Banner & Interactive Quick Analyzer
        banner = ctk.CTkFrame(container, fg_color=C_BG_CARD, corner_radius=10, border_color=C_BORDER, border_width=1)
        banner.grid(row=0, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        banner.grid_columnconfigure(0, weight=1)

        b_top = ctk.CTkFrame(banner, fg_color="transparent")
        b_top.pack(fill="x", padx=16, pady=12)

        ctk.CTkLabel(
            b_top, text="📊  Wordlist Analytics Dashboard",
            font=ctk.CTkFont(size=14, weight="bold"), text_color=C_TEXT_MAIN
        ).pack(side="left")

        ctk.CTkButton(
            b_top, text="📂 Analyze Any .txt File", width=160, height=30, corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"), fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            command=self._action_load_file_for_stats
        ).pack(side="right")

        # KPI Summary Cards Row
        stat_kpi_row = ctk.CTkFrame(container, fg_color="transparent")
        stat_kpi_row.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 10), sticky="ew")
        stat_kpi_row.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._s_kpi_total = self._create_kpi_card(stat_kpi_row, "Total Words Analyzed", "—", 0, C_ACCENT)
        self._s_kpi_len   = self._create_kpi_card(stat_kpi_row, "Average Length", "—", 1, C_SUCCESS)
        self._s_kpi_ent   = self._create_kpi_card(stat_kpi_row, "Average Shannon Entropy", "—", 2, C_PURPLE)
        self._s_kpi_tier  = self._create_kpi_card(stat_kpi_row, "High-Strength Passwords", "—", 3, C_WARN)

        # Charts Row (Pure Native Widgets - zero lag, 100% Light/Dark compatible!)
        # Chart 1: Word Length Distribution
        c_len = self._create_card(container, "📏  Word Length Distribution", row=2, col=0)
        c_len.grid_columnconfigure(0, weight=1)
        self._box_len_chart = ctk.CTkFrame(c_len, fg_color="transparent")
        self._box_len_chart.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self._render_empty_chart(self._box_len_chart, "Generate a wordlist or click 'Analyze Any .txt File' above.")

        # Chart 2: Top Character Frequency
        c_char = self._create_card(container, "🔤  Top Character Distribution", row=2, col=1)
        c_char.grid_columnconfigure(0, weight=1)
        self._box_char_chart = ctk.CTkFrame(c_char, fg_color="transparent")
        self._box_char_chart.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self._render_empty_chart(self._box_char_chart, "Generate a wordlist or click 'Analyze Any .txt File' above.")

        # Chart 3: Structural Pattern Breakdown
        c_pat = self._create_card(container, "🎯  Pattern Composition & Modifiers", row=3, col=0, colspan=2)
        c_pat.grid_columnconfigure(0, weight=1)
        self._box_pat_chart = ctk.CTkFrame(c_pat, fg_color="transparent")
        self._box_pat_chart.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self._render_empty_chart(self._box_pat_chart, "Pattern percentages will appear here once generated.")

        return container

    # ══════════════════════════════════════════════════════════════════════════
    # VIEW 3: ENTROPY INSPECTOR & STRENGTH ANALYZER
    # ══════════════════════════════════════════════════════════════════════════
    def _build_view_entropy(self) -> ctk.CTkScrollableFrame:
        container = ctk.CTkScrollableFrame(self._viewport, fg_color="transparent", corner_radius=0)
        container.grid_columnconfigure(0, weight=1)

        # ── Interactive Live Password Strength Tester ─────────────────────────
        live_card = self._create_card(container, "🧪  Interactive Real-Time Password Tester", row=0, col=0)
        live_card.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(
            live_card, text="Type any word or password to test its Shannon entropy & crack resistance in real time:",
            font=ctk.CTkFont(size=12), text_color=C_TEXT_MUTED
        ).grid(row=0, column=0, columnspan=3, padx=10, pady=(2, 6), sticky="w")

        self._live_entry = ctk.CTkEntry(
            live_card, placeholder_text="Type password to test... (e.g. John@1990!pass)",
            height=38, corner_radius=6, fg_color=C_INPUT_BG, border_color=C_INPUT_BORDER,
            text_color=C_TEXT_MAIN
        )
        self._live_entry.grid(row=1, column=0, columnspan=2, padx=(10, 6), pady=6, sticky="ew")
        self._live_entry.bind("<KeyRelease>", self._on_live_tester_type)

        self._live_tier_badge = ctk.CTkLabel(
            live_card, text="Entropy: 0.00 bits | Waiting...",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=C_TEXT_MUTED
        )
        self._live_tier_badge.grid(row=1, column=2, padx=(6, 10), pady=6, sticky="w")

        # ── Password Strength Ranking & Filter Card ───────────────────────────
        tbl_card = self._create_card(container, "🔐  Ranked Password Matrix & Strength Filtering", row=1, col=0)
        tbl_card.grid_columnconfigure(0, weight=1)

        t_bar = ctk.CTkFrame(tbl_card, fg_color="transparent")
        t_bar.grid(row=0, column=0, padx=8, pady=(0, 8), sticky="ew")
        t_bar.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            t_bar, text="Filter by Strength Tier:",
            font=ctk.CTkFont(size=12, weight="bold"), text_color=C_TEXT_MAIN
        ).pack(side="left", padx=(0, 10))

        self._tier_filter_btn = ctk.CTkSegmentedButton(
            t_bar, values=["All", "Weak", "Fair", "Strong", "Excellent"],
            height=28, corner_radius=6, font=ctk.CTkFont(size=11),
            selected_color=C_ACCENT, selected_hover_color=C_ACCENT_HOVER,
            command=self._on_tier_filter_change
        )
        self._tier_filter_btn.set("All")
        self._tier_filter_btn.pack(side="left", padx=4)

        self._btn_export_tier = ctk.CTkButton(
            t_bar, text="💾 Export Selected Tier", width=140, height=28, corner_radius=6,
            font=ctk.CTkFont(size=11, weight="bold"), fg_color=C_ACCENT, hover_color=C_ACCENT_HOVER,
            command=self._action_export_filtered_tier
        )
        self._btn_export_tier.pack(side="right", padx=4)

        # Results Table List
        self._table_box = ctk.CTkScrollableFrame(
            tbl_card, height=320, corner_radius=8,
            fg_color=C_BG_SUB_CARD, border_color=C_BORDER, border_width=1
        )
        self._table_box.grid(row=1, column=0, padx=8, pady=(0, 8), sticky="nsew")
        self._table_box.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self._render_empty_table(self._table_box)
        return container

    def _on_live_tester_type(self, event=None):
        text = self._live_entry.get().strip()
        if not text:
            self._live_tier_badge.configure(text="Entropy: 0.00 bits | Waiting...", text_color=C_TEXT_MUTED)
            return
        score = shannon_entropy(text)
        tier  = strength_tier(score)
        colors = {"Weak": C_ERR, "Fair": C_WARN, "Strong": C_SUCCESS, "Excellent": C_PURPLE}
        self._live_tier_badge.configure(
            text=f"Entropy: {score:.3f} bits | Tier: {tier}",
            text_color=colors.get(tier, C_ACCENT)
        )

    # ══════════════════════════════════════════════════════════════════════════
    # VIEW 4: USER GUIDE & COMBINATION RULES
    # ══════════════════════════════════════════════════════════════════════════
    def _build_view_guide(self) -> ctk.CTkScrollableFrame:
        container = ctk.CTkScrollableFrame(self._viewport, fg_color="transparent", corner_radius=0)
        container.grid_columnconfigure(0, weight=1)

        g_card = self._create_card(container, "📖  Engine Architecture & Permutation Rules", row=0, col=0)
        g_card.grid_columnconfigure(0, weight=1)

        guide_content = (
            "CipherForge combines user profile seeds using high-probability permutation logic:\n\n"
            "1. Structural Root Combinations:\n"
            "   • Name + Year (john1990, john90)\n"
            "   • Name + Pet (johnmax, maxjohn)\n"
            "   • Pet + Year (max1990, max90)\n"
            "   • Name + Pet + Year (johnmax1990)\n"
            "   • Name + City + Year (johnlondon1990)\n"
            "   • Name + Special + Year (john@1990, john!1990, ...)\n"
            "   • All inputs combined (johnkhanmaxlondon...)\n\n"
            "2. Case Mutations:\n"
            "   • lowercase, UPPERCASE, Capitalized, aLtErNaTiNg, AlTeRnAtInG\n\n"
            "3. Bounded Leetspeak (Zero-Explosion Algorithm):\n"
            "   • a → @, 4  |  e → 3, €  |  i → 1, !  |  o → 0, °\n"
            "   • s → $, 5  |  t → 7, +  |  b → 8  |  g → 9\n\n"
            "4. Prefixes & Suffixes:\n"
            "   • Prefixes: admin_, user_, root_, hack_, pass_, secret_\n"
            "   • Suffixes: 123, 007, 69, 420, 2024, 2025, 2026, specials (!, @, #, $, ...), and years."
        )

        ctk.CTkLabel(
            g_card, text=guide_content, justify="left",
            font=ctk.CTkFont(family="Cascadia Code, Consolas", size=12),
            text_color=C_TEXT_MAIN
        ).pack(padx=16, pady=16, anchor="w")

        return container

    # ══════════════════════════════════════════════════════════════════════════
    # UI CONSTRUCTION HELPERS (Cards, Badges, Charts)
    # ══════════════════════════════════════════════════════════════════════════
    def _create_card(self, parent, title: str, row: int, col: int, colspan: int = 1) -> ctk.CTkFrame:
        outer = ctk.CTkFrame(parent, fg_color=C_BG_CARD, corner_radius=10, border_color=C_BORDER, border_width=1)
        outer.grid(row=row, column=col, columnspan=colspan, padx=10, pady=8, sticky="nsew")

        hdr = ctk.CTkFrame(outer, fg_color="transparent")
        hdr.pack(fill="x", padx=14, pady=(12, 6))

        pill = ctk.CTkFrame(hdr, width=4, height=18, fg_color=C_ACCENT, corner_radius=2)
        pill.pack(side="left", padx=(0, 8))
        pill.pack_propagate(False)

        ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(size=13, weight="bold"), text_color=C_TEXT_MAIN).pack(side="left")

        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=8, pady=(0, 10))
        return inner

    def _create_kpi_cell(self, parent, title: str, val: str, col: int, color: str):
        cell = ctk.CTkFrame(parent, fg_color="transparent")
        cell.grid(row=0, column=col, padx=10, pady=8, sticky="ew")
        ctk.CTkLabel(cell, text=title, font=ctk.CTkFont(size=9, weight="bold"), text_color=C_TEXT_MUTED).pack()
        lbl = ctk.CTkLabel(cell, text=val, font=ctk.CTkFont(size=14, weight="bold"), text_color=color)
        lbl.pack()
        return lbl

    def _create_kpi_card(self, parent, title: str, val: str, col: int, color: str):
        card = ctk.CTkFrame(parent, fg_color=C_BG_CARD, corner_radius=8, border_color=C_BORDER, border_width=1)
        card.grid(row=0, column=col, padx=6, pady=4, sticky="ew")
        ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=C_TEXT_MUTED).pack(pady=(10, 2))
        lbl = ctk.CTkLabel(card, text=val, font=ctk.CTkFont(size=18, weight="bold"), text_color=color)
        lbl.pack(pady=(0, 10))
        return lbl

    def _render_empty_chart(self, container: ctk.CTkFrame, msg: str):
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            container, text=f"ℹ  {msg}",
            font=ctk.CTkFont(size=11), text_color=C_TEXT_MUTED
        ).pack(pady=40)

    def _render_empty_table(self, container: ctk.CTkFrame):
        for w in container.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            container, text="No generated words available.\nRun the generator or click 'Analyze Any .txt File' in Statistics.",
            font=ctk.CTkFont(size=11), text_color=C_TEXT_MUTED
        ).pack(pady=40)

    # ══════════════════════════════════════════════════════════════════════════
    # ACTIONS & ENGINE INTEGRATION
    # ══════════════════════════════════════════════════════════════════════════
    def _action_fill_demo(self):
        demo = {
            'name': 'john', 'last': 'khan', 'year': '1990',
            'pet': 'max', 'city': 'london', 'color': 'blue', 'sport': 'cricket',
            'min_len': '6', 'max_len': '20', 'output': '',
        }
        for k, v in demo.items():
            if k in self._inputs:
                self._inputs[k].delete(0, "end")
                self._inputs[k].insert(0, v)
        self._log_msg("✨  Populated form with demo target attributes.", C_ACCENT)

    def _action_clear_console(self):
        self._console.configure(state="normal")
        self._console.delete("1.0", "end")
        self._console.configure(state="disabled")

    def _log_msg(self, text: str, color: str = ""):
        self._console.configure(state="normal")
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._console.insert("end", f"[{ts}] {text}\n")
        self._console.see("end")
        self._console.configure(state="disabled")

    def _get_form_profile(self) -> dict | None:
        data = {k: e.get().strip() for k, e in self._inputs.items()}
        if not data.get('name'):
            self._log_msg("✖ Error: First Name is required.", C_ERR)
            return None
        year = data.get('year', '')
        if not year or not year.isdigit() or len(year) != 4:
            self._log_msg("✖ Error: Birth Year must be 4 digits (e.g. 1990).", C_ERR)
            return None
        try:
            data['min_len'] = int(data.get('min_len') or DEFAULT_MIN_LEN)
            data['max_len'] = int(data.get('max_len') or DEFAULT_MAX_LEN)
            if data['min_len'] > data['max_len']:
                self._log_msg("✖ Error: Min Length cannot exceed Max Length.", C_ERR)
                return None
        except ValueError:
            self._log_msg("✖ Error: Min/Max length must be integers.", C_ERR)
            return None
        data['leet_max'] = int(self._leet_slider.get())
        return data

    def _action_estimate_count(self):
        profile = self._get_form_profile()
        if not profile:
            return
        est = estimate_count(profile, profile['leet_max'])
        bases = build_base_candidates(profile)
        self._log_msg(f"🔢  Forecast: {len(bases)} root combinations → ~{est:,} candidate checks.", C_ACCENT)
        self._lbl_status.configure(text=f"Estimated ~{est:,} candidate combinations")

    def _action_start_generation(self):
        profile = self._get_form_profile()
        if not profile:
            return

        self._action_clear_console()
        self._log_msg(f"⚡  Starting CipherForge synthesis for target: '{profile['name']}'...", C_ACCENT)

        self._btn_generate.configure(state="disabled")
        self._btn_estimate.configure(state="disabled")
        self._btn_stop.configure(state="normal")
        self._progress_bar.set(0)
        self._lbl_status.configure(text="Synthesizing wordlist combinations...")
        self._side_status_lbl.configure(text="● Synthesizing...", text_color=C_WARN)

        self._is_generating = True
        self._stop_event.clear()

        def worker():
            def cb(p):
                self._log_queue.put(('progress', p))

            result = run_pipeline(
                profile,
                progress_cb=cb,
                stop_event=self._stop_event,
                leet_max=profile['leet_max'],
                min_len=profile['min_len'],
                max_len=profile['max_len'],
                output_path=profile.get('output') or None
            )
            self._log_queue.put(('complete', result))

        threading.Thread(target=worker, daemon=True).start()

    def _action_stop_generation(self):
        self._stop_event.set()
        self._lbl_status.configure(text="Aborting...")
        self._log_msg("⛔  Abort signal dispatched to engine thread...", C_WARN)

    def _action_open_folder(self):
        target = self._last_file or os.getcwd()
        folder = os.path.dirname(os.path.abspath(target)) if os.path.isfile(target) else os.path.abspath(target)
        try:
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", folder])
            else:
                subprocess.Popen(["xdg-open", folder])
            self._log_msg(f"📂  Opened output folder: {folder}", C_SUCCESS)
        except Exception as e:
            self._log_msg(f"✖  Failed to open directory: {e}", C_ERR)

    def _action_load_file_for_stats(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(title="Select Wordlist File", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                words = {line.strip() for line in f if line.strip()}
            self._apply_analysis_to_ui(words, path)
            self._log_msg(f"📊  Imported & analyzed: {path} ({len(words):,} words)", C_SUCCESS)
        except Exception as e:
            self._log_msg(f"✖  Failed to load file: {e}", C_ERR)

    # ── Non-Blocking Worker Queue Polling ──────────────────────────────────────
    def _poll_worker_queue(self):
        batch = 0
        while batch < 20:
            try:
                kind, payload = self._log_queue.get_nowait()
                batch += 1
            except queue.Empty:
                break

            if kind == 'progress':
                pct = float(payload.get('pct', 0))
                self._progress_bar.set(pct)
                detail = payload.get('detail', '')
                self._lbl_status.configure(text=detail)
                self._log_msg(detail)

            elif kind == 'complete':
                res = payload
                self._is_generating = False
                self._btn_generate.configure(state="normal")
                self._btn_estimate.configure(state="normal")
                self._btn_stop.configure(state="disabled")

                if res['count'] == 0:
                    self._progress_bar.set(0)
                    self._lbl_status.configure(text="No words matched the length filters.")
                    self._side_status_lbl.configure(text="● Engine Ready", text_color=C_SUCCESS)
                    self._log_msg("⚠  Zero words matched length boundaries. Try widening Min/Max.", C_WARN)
                else:
                    self._progress_bar.set(1.0)
                    self._last_file = res['file']
                    self._last_result = res
                    count_str = f"{res['count']:,}"

                    self._kpi_words.configure(text=count_str)
                    self._kpi_time.configure(text=f"{res['elapsed']:.2f}s")
                    self._kpi_speed.configure(text=f"{res['rate']:,}/s")
                    self._kpi_file.configure(text=os.path.basename(res['file']) if res.get('file') else "done")

                    self._side_status_lbl.configure(text="● Complete ✓", text_color=C_SUCCESS)
                    self._side_words_lbl.configure(text=f"{count_str} words ready")
                    self._lbl_status.configure(text=f"Done — Generated {count_str} words in {res['elapsed']:.2f}s")

                    self._log_msg(f"✅  Generation complete: {count_str} words written to disk!", C_SUCCESS)
                    if res.get('file'):
                        self._log_msg(f"    File: {res['file']}", C_SUCCESS)

                    # Update Analytics & Entropy tabs
                    wordlist_set = res.get('wordlist', set())
                    self._apply_analysis_to_ui(wordlist_set, res.get('file', 'Generated Wordlist'))

        # Poll smoothly (80ms when running, 300ms when idle to eliminate lag)
        next_poll = 80 if self._is_generating else 300
        self.after(next_poll, self._poll_worker_queue)

    # ── Update UI with Analytics Data ─────────────────────────────────────────
    def _apply_analysis_to_ui(self, words: set[str], source_name: str):
        if not words:
            return
        analysis = analyze_wordlist(words)
        self._last_analysis = analysis

        # 1. Update Statistics KPIs
        self._s_kpi_total.configure(text=f"{analysis.total_words:,}")
        self._s_kpi_len.configure(text=f"{analysis.avg_length:.1f} chars")
        self._s_kpi_ent.configure(text=f"{analysis.avg_entropy:.2f} bits")
        strong_cnt = analysis.strength_tiers.get('Strong', 0) + analysis.strength_tiers.get('Excellent', 0)
        self._s_kpi_tier.configure(text=f"{strong_cnt:,}")

        # 2. Render Native Chart: Word Length Distribution
        for w in self._box_len_chart.winfo_children():
            w.destroy()
        len_items = sorted(analysis.length_distribution.items(), key=lambda x: x[1], reverse=True)[:8]
        max_len_val = max((v for _, v in len_items), default=1) or 1
        for l_val, cnt in len_items:
            row = ctk.CTkFrame(self._box_len_chart, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{l_val} chars", width=65, font=ctk.CTkFont(size=11), text_color=C_TEXT_MUTED).pack(side="left")
            p = ctk.CTkProgressBar(row, height=8, corner_radius=4, progress_color=C_ACCENT, fg_color=C_BORDER)
            p.set(cnt / max_len_val)
            p.pack(side="left", fill="x", expand=True, padx=8)
            ctk.CTkLabel(row, text=f"{cnt:,}", width=60, font=ctk.CTkFont(size=11, weight="bold"), text_color=C_TEXT_MAIN).pack(side="right")

        # 3. Render Native Chart: Top Characters
        for w in self._box_char_chart.winfo_children():
            w.destroy()
        char_items = list(analysis.char_frequency.items())[:8]
        max_char_val = max((v for _, v in char_items), default=1) or 1
        for char, cnt in char_items:
            row = ctk.CTkFrame(self._box_char_chart, fg_color="transparent")
            row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"'{char}'", width=65, font=ctk.CTkFont(family="Consolas", size=11, weight="bold"), text_color=C_SUCCESS).pack(side="left")
            p = ctk.CTkProgressBar(row, height=8, corner_radius=4, progress_color=C_SUCCESS, fg_color=C_BORDER)
            p.set(cnt / max_char_val)
            p.pack(side="left", fill="x", expand=True, padx=8)
            ctk.CTkLabel(row, text=f"{cnt:,}", width=60, font=ctk.CTkFont(size=11, weight="bold"), text_color=C_TEXT_MAIN).pack(side="right")

        # 4. Render Native Chart: Pattern Breakdown
        for w in self._box_pat_chart.winfo_children():
            w.destroy()
        p_grid = ctk.CTkFrame(self._box_pat_chart, fg_color="transparent")
        p_grid.pack(fill="x", padx=4, pady=4)
        p_grid.grid_columnconfigure((0, 1), weight=1)

        for idx, (label, pct) in enumerate(analysis.pattern_breakdown.items()):
            cell = ctk.CTkFrame(p_grid, fg_color=C_BG_SUB_CARD, corner_radius=6, border_color=C_BORDER, border_width=1)
            cell.grid(row=idx // 2, column=idx % 2, padx=6, pady=4, sticky="ew")
            ctk.CTkLabel(cell, text=label, font=ctk.CTkFont(size=11), text_color=C_TEXT_MUTED).pack(anchor="w", padx=8, pady=(6, 2))
            bar_row = ctk.CTkFrame(cell, fg_color="transparent")
            bar_row.pack(fill="x", padx=8, pady=(0, 6))
            p = ctk.CTkProgressBar(bar_row, height=8, corner_radius=4, progress_color=C_PURPLE, fg_color=C_BORDER)
            p.set(pct / 100.0)
            p.pack(side="left", fill="x", expand=True, padx=(0, 8))
            ctk.CTkLabel(bar_row, text=f"{pct:.1f}%", font=ctk.CTkFont(size=11, weight="bold"), text_color=C_TEXT_MAIN).pack(side="right")

        # 5. Populate Entropy Table
        self._populate_entropy_table(analysis.entropy_scores)

    def _populate_entropy_table(self, scored_words: list[tuple[str, float]], filter_tier: str = "All"):
        for w in self._table_box.winfo_children():
            w.destroy()

        if not scored_words:
            self._render_empty_table(self._table_box)
            return

        # Header Row
        hdr = ctk.CTkFrame(self._table_box, fg_color="transparent")
        hdr.grid(row=0, column=0, columnspan=4, sticky="ew", padx=6, pady=(4, 2))
        hdr.grid_columnconfigure((0, 1, 2, 3), weight=1)
        for c_idx, title in enumerate(["#", "Word", "Entropy (bits)", "Strength Tier"]):
            ctk.CTkLabel(hdr, text=title, font=ctk.CTkFont(size=11, weight="bold"), text_color=C_ACCENT).grid(row=0, column=c_idx, sticky="w")

        ctk.CTkFrame(self._table_box, height=1, fg_color=C_BORDER).grid(row=1, column=0, columnspan=4, sticky="ew", padx=4, pady=(0, 4))

        # Filter
        items = scored_words
        if filter_tier != "All":
            items = [(w, e) for w, e in items if strength_tier(e) == filter_tier]

        tier_colors = {"Weak": C_ERR, "Fair": C_WARN, "Strong": C_SUCCESS, "Excellent": C_PURPLE}

        # Show top 150 rows smoothly
        for idx, (word, score) in enumerate(items[:150], start=1):
            tier = strength_tier(score)
            color = tier_colors.get(tier, C_TEXT_MAIN)
            r = ctk.CTkFrame(self._table_box, fg_color="transparent")
            r.grid(row=idx + 1, column=0, columnspan=4, sticky="ew", padx=6, pady=1)
            r.grid_columnconfigure((0, 1, 2, 3), weight=1)

            ctk.CTkLabel(r, text=str(idx), font=ctk.CTkFont(size=10), text_color=C_TEXT_MUTED).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(r, text=word, font=ctk.CTkFont(family="Consolas", size=11), text_color=C_TEXT_MAIN).grid(row=0, column=1, sticky="w")
            ctk.CTkLabel(r, text=f"{score:.3f}", font=ctk.CTkFont(size=11), text_color=C_TEXT_MUTED).grid(row=0, column=2, sticky="w")
            ctk.CTkLabel(r, text=tier, font=ctk.CTkFont(size=11, weight="bold"), text_color=color).grid(row=0, column=3, sticky="w")

    def _on_tier_filter_change(self, choice: str):
        if not self._last_analysis or not self._last_analysis.entropy_scores:
            return
        self._populate_entropy_table(self._last_analysis.entropy_scores, filter_tier=choice)

    def _action_export_filtered_tier(self):
        if not self._last_analysis or not self._last_analysis.entropy_scores:
            self._log_msg("✖ No wordlist loaded to export.", C_WARN)
            return

        choice = self._tier_filter_btn.get()
        items = self._last_analysis.entropy_scores
        if choice != "All":
            items = [(w, e) for w, e in items if strength_tier(e) == choice]

        if not items:
            self._log_msg(f"✖ No words match tier '{choice}'.", C_WARN)
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_name = f"cipherforge_tier_{choice.lower()}_{ts}.txt"
        try:
            with open(out_name, 'w', encoding='utf-8') as f:
                for word, _ in items:
                    f.write(word + "\n")
            abs_p = os.path.abspath(out_name)
            self._log_msg(f"💾  Exported {len(items):,} '{choice}' words to: {abs_p}", C_SUCCESS)
            self._btn_export_tier.configure(text=f"✅ Saved {len(items):,}")
            self.after(2500, lambda: self._btn_export_tier.configure(text="💾 Export Selected Tier"))
        except Exception as e:
            self._log_msg(f"✖  Export failed: {e}", C_ERR)


if __name__ == "__main__":
    app = CipherForgeApp()
    app.mainloop()
