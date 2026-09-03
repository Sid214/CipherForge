"""
cipherforge/gui/app_qt.py
CipherForge Studio — Modern, Responsive, GPU-Accelerated PyQt6 Desktop Suite.
Engineered for zero-lag responsiveness, seamless Light/Dark mode, and advanced wordlist synthesis.
"""
from __future__ import annotations

import sys
import os
import random
import datetime
import threading
from typing import Callable

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QLineEdit, QSlider, QProgressBar,
    QScrollArea, QPlainTextEdit, QStackedWidget, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QComboBox, QListView, QSizePolicy
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QRect, QSize, QTimer, QPoint
from PyQt6.QtGui import (
    QColor, QPainter, QLinearGradient, QFont, QPixmap, QBrush, QPen, QCursor, QPalette
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from cipherforge.core.generator import (
    run_pipeline, estimate_count, build_base_candidates, get_output_dir
)
from cipherforge.core.analyzer import (
    analyze_wordlist, shannon_entropy, strength_tier
)
from cipherforge.core.rules import DEFAULT_MIN_LEN, DEFAULT_MAX_LEN

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets")
CHEVRON_PATH = os.path.join(ASSETS, "chevron_down.png").replace("\\", "/")

DARK = dict(
    app_bg="#0B0F19",
    sidebar_bg="#0F172A",
    card_bg="#131F37",
    card_bg2="#0A1120",
    input_bg="#070C18",
    border="#1E293B",
    border2="#334155",
    text="#F8FAFC",
    text_sub="#94A3B8",
    text_muted="#64748B",
    accent="#2563EB",
    accent_dark="#1D4ED8",
    accent_glow="#38BDF8",
    success="#10B981",
    warn="#F59E0B",
    danger="#EF4444",
    purple="#8B5CF6",
    bar_track="#1E293B",
    console_bg="#050811",
    console_text="#38BDF8",
    nav_hover="#1E293B",
    nav_active_bg="#1E3A8A",
    progress_bg="#1E293B",
)

LIGHT = dict(
    app_bg="#F8FAFC",
    sidebar_bg="#FFFFFF",
    card_bg="#FFFFFF",
    card_bg2="#F1F5F9",
    input_bg="#FFFFFF",
    border="#E2E8F0",
    border2="#CBD5E1",
    text="#0F172A",
    text_sub="#475569",
    text_muted="#94A3B8",
    accent="#2563EB",
    accent_dark="#1D4ED8",
    accent_glow="#60A5FA",
    success="#059669",
    warn="#D97706",
    danger="#DC2626",
    purple="#7C3AED",
    bar_track="#E2E8F0",
    console_bg="#0F172A",
    console_text="#38BDF8",
    nav_hover="#F1F5F9",
    nav_active_bg="#DBEAFE",
    progress_bg="#E2E8F0",
)

INDIAN_FIRST_NAMES = [
    "Aarav", "Rohan", "Aditya", "Vihaan", "Arjun", "Kabir", "Aryan", "Reyansh",
    "Ananya", "Diya", "Isha", "Rhea", "Pooja", "Priya", "Neha",
    "Kunal", "Rahul", "Varun", "Vikram", "Sneha", "Tanvi", "Sanya", "Kavya",
    "Amit", "Nikhil", "Gaurav", "Suresh", "Manish", "Deepak", "Shreya", "Meera"
]

INDIAN_LAST_NAMES = [
    "Sharma", "Verma", "Gupta", "Malhotra", "Mehta", "Chopra", "Kulkarni",
    "Joshi", "Deshmukh", "Deshpande", "Bhatia", "Reddy", "Nair", "Iyer", "Rao",
    "Kapoor", "Khan", "Singh", "Yadav", "Pandey", "Chauhan", "Agarwal", "Bansal"
]

INDIAN_CITIES = [
    "Mumbai", "Pune", "Delhi", "Bengaluru", "Hyderabad", "Chennai", "Kolkata",
    "Ahmedabad", "Jaipur", "Surat", "Lucknow", "Nagpur", "Indore", "Thane", "Nashik"
]

INDIAN_PETS = ["Bruno", "Simba", "Rocky", "Leo", "Tiger", "Max", "Buddy", "Sheru", "Tommy", "Coco"]
INDIAN_COLORS = ["Blue", "Black", "Red", "Green", "White", "Saffron", "Navy", "Gold"]
INDIAN_SPORTS = ["Cricket", "Football", "Badminton", "Kabaddi", "Chess", "Tennis", "Hockey"]
RELATIONS = ["Spouse", "Child", "Sibling", "Parent", "Close Friend", "Other"]


class DropdownComboBox(QComboBox):
    """
    Custom QComboBox that dynamically positions its popup menu strictly below
    the selection field, matching the exact width and alignment of the field,
    keeping the selected field fully visible above without covering it.
    """
    def showPopup(self):
        super().showPopup()
        container = self.view().parentWidget()
        if container:
            p = self.mapToGlobal(QPoint(0, self.height()))
            container.move(p.x(), p.y())
            container.resize(self.width(), container.height())
            QTimer.singleShot(0, lambda: container.move(p.x(), p.y()) if container else None)

def _qss(t: dict) -> str:
    return f"""
QMainWindow, QWidget {{
    background-color: {t['app_bg']};
    color: {t['text']};
    font-family: "Segoe UI", Arial, sans-serif;
}}
QFrame#sidebar {{
    background-color: {t['sidebar_bg']};
    border-right: 1px solid {t['border']};
}}
QFrame#sidebar QWidget, QFrame#sidebar QLabel {{
    background-color: transparent;
    background: transparent;
}}

QFrame#card {{
    background-color: {t['card_bg']};
    border: 1px solid {t['border']};
    border-radius: 10px;
}}
QFrame#card2 {{
    background-color: {t['card_bg2']};
    border: 1px solid {t['border']};
    border-radius: 8px;
}}

QScrollArea {{
    background-color: {t['app_bg']};
    background: transparent;
    border: none;
}}
QScrollArea > QWidget > QWidget {{
    background-color: {t['app_bg']};
}}

QLabel {{
    color: {t['text']};
    background: transparent;
}}
QLabel#h1 {{
    font-size: 19px;
    font-weight: 700;
}}
QLabel#tag {{
    font-size: 10px;
    font-weight: 700;
    color: {t['text_muted']};
    letter-spacing: 1px;
}}
QLabel#muted {{
    font-size: 11px;
    color: {t['text_muted']};
}}
QLabel#card_title {{
    font-size: 13px;
    font-weight: 600;
    color: {t['text']};
}}
QLabel#kpi_accent {{ font-size: 17px; font-weight: 700; color: {t['accent']}; }}
QLabel#kpi_success {{ font-size: 17px; font-weight: 700; color: {t['success']}; }}
QLabel#kpi_warn {{ font-size: 17px; font-weight: 700; color: {t['warn']}; }}
QLabel#kpi_purple {{ font-size: 17px; font-weight: 700; color: {t['purple']}; }}

QLineEdit {{
    background-color: {t['input_bg']};
    border: 1.5px solid {t['border2']};
    border-radius: 7px;
    color: {t['text']};
    font-size: 12px;
    padding: 6px 10px;
    selection-background-color: {t['accent']};
}}
QLineEdit:focus {{
    border-color: {t['accent']};
    background-color: {t['card_bg']};
}}

/* QComboBox: Single clean control */
QComboBox {{
    background-color: {t['input_bg']};
    border: 1.5px solid {t['border2']};
    border-radius: 7px;
    color: {t['text']};
    font-size: 12px;
    font-weight: 600;
    padding: 5px 28px 5px 12px;
    max-height: 34px;
}}
QComboBox:hover {{
    border-color: {t['accent']};
}}
QComboBox:focus {{
    border-color: {t['accent']};
}}
QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
    border-top-right-radius: 7px;
    border-bottom-right-radius: 7px;
    background: transparent;
}}
QComboBox::down-arrow {{
    image: url("{CHEVRON_PATH}");
    width: 12px;
    height: 12px;
    margin-right: 6px;
}}

/* Dropdown Popup: One single opaque popup with clean border and rounded corners */
QComboBox QFrame {{
    border: none;
    background: transparent;
    padding: 0px;
    margin: 0px;
}}
QComboBox QAbstractItemView, QComboBox QListView {{
    background-color: {t['card_bg']};
    color: {t['text']};
    border: 1.5px solid {t['border2']};
    border-radius: 8px;
    padding: 4px;
    outline: 0px;
    selection-background-color: {t['accent']};
    selection-color: #FFFFFF;
}}
QComboBox QAbstractItemView::item, QComboBox QListView::item {{
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 22px;
    color: {t['text']};
    background-color: transparent;
}}
QComboBox QAbstractItemView::item:hover, QComboBox QListView::item:hover {{
    background-color: {t['nav_hover']};
    color: {t['text']};
}}
QComboBox QAbstractItemView::item:selected, QComboBox QListView::item:selected {{
    background-color: {t['accent']};
    color: #FFFFFF;
}}

QSlider::groove:horizontal {{
    height: 4px;
    border-radius: 2px;
    background: {t['border']};
}}
QSlider::sub-page:horizontal {{
    background: {t['accent']};
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    width: 14px;
    height: 14px;
    border-radius: 7px;
    background: {t['accent']};
    margin: -5px 0;
}}

QProgressBar {{
    background-color: {t['progress_bg']};
    border: none;
    border-radius: 4px;
    text-align: center;
    height: 8px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t['accent']}, stop:1 {t['accent_glow']});
    border-radius: 4px;
}}

/* Button Primary: Always solid electric blue */
QPushButton#btn_primary {{
    background-color: {t['accent']};
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t['accent']}, stop:1 {t['accent_dark']});
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 700;
    padding: 10px 22px;
    min-height: 22px;
}}
QPushButton#btn_primary:hover {{
    background-color: {t['accent_glow']};
    background: {t['accent_glow']};
}}
QPushButton#btn_primary:pressed {{
    background-color: {t['accent_dark']};
    background: {t['accent_dark']};
}}
QPushButton#btn_primary:disabled {{
    background-color: {t['border']};
    background: {t['border']};
    color: {t['text_muted']};
}}

QPushButton#btn_secondary {{
    background-color: {t['card_bg2']};
    color: {t['accent']};
    border: 1.5px solid {t['border2']};
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 18px;
    min-height: 18px;
}}
QPushButton#btn_secondary:hover {{
    background-color: {t['nav_hover']};
    border-color: {t['accent']};
}}
QPushButton#btn_secondary:disabled {{
    color: {t['text_muted']};
    border-color: {t['border']};
}}

/* Button Danger: Stop Button with clean minimal red styling */
QPushButton#btn_danger {{
    background-color: transparent;
    color: {t['danger']};
    border: 1.5px solid {t['danger']};
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    padding: 8px 18px;
    min-height: 18px;
    text-align: center;
}}
QPushButton#btn_danger:hover {{
    background-color: {t['danger']};
    color: white;
}}
QPushButton#btn_danger:disabled {{
    color: {t['text_muted']};
    border-color: {t['border']};
}}

QPushButton#btn_ghost {{
    background-color: {t['card_bg2']};
    color: {t['text_sub']};
    border: 1px solid {t['border2']};
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 14px;
    min-height: 18px;
}}
QPushButton#btn_ghost:hover {{
    background-color: {t['nav_hover']};
    color: {t['text']};
    border-color: {t['accent']};
}}

/* Sleek Terminal Clear Button */
QPushButton#terminal_btn {{
    background-color: transparent;
    color: {t['console_text']};
    border: 1px solid {t['border2']};
    border-radius: 5px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 11px;
    font-weight: 600;
    padding: 4px 12px;
    min-height: 18px;
}}
QPushButton#terminal_btn:hover {{
    background-color: {t['card_bg2']};
    border-color: {t['accent']};
    color: {t['text']};
}}

QPushButton#nav_btn {{
    background-color: transparent;
    color: {t['text_sub']};
    border: none;
    border-radius: 8px;
    font-size: 12px;
    font-weight: 600;
    padding: 10px 14px;
    text-align: left;
}}
QPushButton#nav_btn:hover {{
    background-color: {t['nav_hover']};
    color: {t['text']};
}}
QPushButton[nav_active="1"]#nav_btn {{
    background-color: {t['nav_active_bg']};
    color: {t['accent']};
    font-weight: 700;
}}

QPushButton#theme_btn {{
    background-color: {t['card_bg2']};
    color: {t['text_sub']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    padding: 6px 10px;
}}
QPushButton#theme_btn:hover {{
    border-color: {t['accent']};
    color: {t['text']};
}}
QPushButton[theme_active="1"]#theme_btn {{
    background-color: {t['accent']};
    color: white;
    border-color: {t['accent']};
}}

QPushButton#tag_btn {{
    background-color: {t['card_bg2']};
    color: {t['text_sub']};
    border: 1px solid {t['border']};
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
    padding: 5px 14px;
    min-height: 18px;
}}
QPushButton#tag_btn:hover {{
    background-color: {t['nav_hover']};
    color: {t['text']};
}}
QPushButton[tag_active="1"]#tag_btn {{
    background-color: {t['accent']};
    color: white;
    border-color: {t['accent']};
}}

QPlainTextEdit#console {{
    background-color: {t['console_bg']};
    color: {t['console_text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    font-family: "Cascadia Code", "Consolas", monospace;
    font-size: 11px;
    padding: 8px;
}}

/* Terminal Scrollbar: Track perfectly matches terminal background with blue thumb */
QPlainTextEdit#console QScrollBar:vertical {{
    background: {t['console_bg']};
    background-color: {t['console_bg']};
    width: 6px;
    border: none;
    margin: 0px;
}}
QPlainTextEdit#console QScrollBar::handle:vertical {{
    background: {t['accent']};
    border-radius: 3px;
    min-height: 24px;
}}
QPlainTextEdit#console QScrollBar::handle:vertical:hover {{
    background: {t['accent_glow']};
}}
QPlainTextEdit#console QScrollBar::add-line:vertical, 
QPlainTextEdit#console QScrollBar::sub-line:vertical,
QPlainTextEdit#console QScrollBar::add-page:vertical, 
QPlainTextEdit#console QScrollBar::sub-page:vertical {{
    background: {t['console_bg']};
    background-color: {t['console_bg']};
    border: none;
    height: 0px;
    width: 0px;
}}

/* Global Scrollbars scoped specifically to general scroll areas */
QScrollArea QScrollBar:vertical,
QTableWidget QScrollBar:vertical {{
    background: {t['app_bg']};
    width: 6px;
    border: none;
    border-radius: 3px;
}}
QScrollArea QScrollBar::handle:vertical,
QTableWidget QScrollBar::handle:vertical {{
    background: {t['border2']};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollArea QScrollBar::handle:vertical:hover,
QTableWidget QScrollBar::handle:vertical:hover {{
    background: {t['accent']};
}}
QScrollArea QScrollBar::add-line:vertical, QScrollArea QScrollBar::sub-line:vertical,
QTableWidget QScrollBar::add-line:vertical, QTableWidget QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QTableWidget {{
    background-color: {t['card_bg2']};
    color: {t['text']};
    border: 1px solid {t['border']};
    border-radius: 8px;
    gridline-color: {t['border']};
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {t['border']};
}}
QHeaderView::section {{
    background-color: {t['card_bg']};
    color: {t['text_sub']};
    border: none;
    border-bottom: 1px solid {t['border2']};
    padding: 8px 10px;
    font-size: 11px;
    font-weight: 600;
}}
"""

class BarChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []
        self._bar = QColor("#2563EB")
        self._track = QColor("#1E293B")
        self._tc = QColor("#94A3B8")
        self._vc = QColor("#F8FAFC")
        self.setMinimumHeight(160)

    def apply_theme(self, t: dict):
        self._bar = QColor(t["accent"])
        self._track = QColor(t["bar_track"])
        self._tc = QColor(t["text_sub"])
        self._vc = QColor(t["text"])
        self.update()

    def set_data(self, data: list[tuple[str, int | float]], color=None):
        self._data = sorted(data, key=lambda x: x[1], reverse=True)[:14]
        if color:
            self._bar = QColor(color)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        if not self._data:
            p.setPen(self._tc)
            p.setFont(QFont("Segoe UI", 11))
            p.drawText(QRect(0, 0, W, H), int(Qt.AlignmentFlag.AlignCenter), "No analysis data loaded yet.")
            p.end()
            return

        lw = 110
        vw = 65
        pad = 10
        gap = 6
        barea = max(W - lw - vw - 20, 20)
        n = len(self._data)
        bh = max(8, min(22, (H - pad * 2 - gap * (n - 1)) // n))
        mv = max(v for _, v in self._data) or 1

        fl = QFont("Segoe UI", 10)
        fb = QFont("Segoe UI", 10)
        fb.setBold(True)

        for i, (lbl, val) in enumerate(self._data):
            y = pad + i * (bh + gap)
            p.setFont(fl)
            p.setPen(self._tc)
            p.drawText(QRect(0, y, lw - 6, bh), int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter), str(lbl)[:14])
            track = QRect(lw, y, barea, bh)
            p.setBrush(self._track)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(track, 3, 3)

            fw = int(barea * (val / mv))
            if fw > 3:
                g = QLinearGradient(float(lw), float(y), float(lw + fw), float(y))
                g.setColorAt(0, self._bar)
                g.setColorAt(1, self._bar.lighter(135))
                p.setBrush(QBrush(g))
                p.drawRoundedRect(QRect(lw, y, fw, bh), 3, 3)

            p.setFont(fb)
            p.setPen(self._vc)
            p.drawText(QRect(lw + barea + 6, y, vw - 4, bh), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), f"{int(val):,}")
        p.end()


class DonutChart(QWidget):
    PAL = ["#2563EB", "#10B981", "#F59E0B", "#8B5CF6", "#EF4444", "#06B6D4", "#F97316"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}
        self._hc = QColor("#0B0F19")
        self._tc = QColor("#94A3B8")
        self.setMinimumHeight(200)

    def apply_theme(self, t: dict):
        self._hc = QColor(t["card_bg"])
        self._tc = QColor(t["text_sub"])
        self.update()

    def set_data(self, data: dict[str, float]):
        self._data = {k: v for k, v in data.items() if v > 0}
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        W, H = self.width(), self.height()
        cx, cy = W // 2, (H - 40) // 2 + 4
        r = min(W, H - 50) // 2 - 10
        ir = int(r * 0.56)

        if not self._data:
            p.setPen(self._tc)
            p.setFont(QFont("Segoe UI", 11))
            p.drawText(QRect(0, 0, W, H), int(Qt.AlignmentFlag.AlignCenter), "No pattern data available.")
            p.end()
            return

        ang = -90 * 16
        for i, (lbl, val) in enumerate(self._data.items()):
            span = int(round(360 * 16 * (val / 100.0)))
            c = QColor(self.PAL[i % len(self.PAL)])
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPie(cx - r, cy - r, r * 2, r * 2, ang, span)
            ang += span

        p.setBrush(self._hc)
        p.setPen(Qt.PenStyle.NoPen)
        p.drawEllipse(cx - ir, cy - ir, ir * 2, ir * 2)

        p.setPen(self._tc)
        p.setFont(QFont("Segoe UI", 10))
        p.drawText(QRect(cx - ir, cy - ir, ir * 2, ir * 2), int(Qt.AlignmentFlag.AlignCenter), f"{len(self._data)}\nfactors")

        ly = cy + r + 10
        iw = W // max(len(self._data), 1)
        p.setFont(QFont("Segoe UI", 9))
        for i, (lbl, val) in enumerate(self._data.items()):
            c = QColor(self.PAL[i % len(self.PAL)])
            lx = i * iw + 4
            p.setBrush(c)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawEllipse(lx, ly + 3, 8, 8)
            p.setPen(self._tc)
            p.drawText(QRect(lx + 12, ly, iw - 14, 18), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter), f"{lbl}: {val:.0f}%")
        p.end()


class GenerationWorker(QThread):
    progress = pyqtSignal(dict)
    complete = pyqtSignal(dict)

    def __init__(self, profile, leet_max, min_len, max_len, output):
        super().__init__()
        self._p = profile
        self._lm = leet_max
        self._mn = min_len
        self._mx = max_len
        self._out = output
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def run(self):
        result = run_pipeline(
            self._p,
            progress_cb=lambda p: self.progress.emit(p),
            stop_event=self._stop,
            leet_max=self._lm,
            min_len=self._mn,
            max_len=self._mx,
            output_path=self._out or None,
        )
        self.complete.emit(result)


class FileAnalysisWorker(QThread):
    finished = pyqtSignal(object, str, str)

    def __init__(self, filepath: str):
        super().__init__()
        self._path = filepath

    def run(self):
        try:
            words = []
            with open(self._path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    w = line.strip()
                    if w:
                        words.append(w)
            if not words:
                self.finished.emit(None, self._path, "File contains no non-empty words.")
                return

            analysis = analyze_wordlist(words)
            self.finished.emit(analysis, self._path, "")
        except Exception as e:
            self.finished.emit(None, self._path, str(e))


def _sep():
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("color: rgba(100, 130, 180, 0.15);")
    return f

def _field(label: str, widget: QWidget) -> QWidget:
    w = QWidget()
    v = QVBoxLayout(w)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(3)
    lbl = QLabel(label)
    lbl.setObjectName("muted")
    fnt = QFont("Segoe UI", 11)
    fnt.setWeight(QFont.Weight.DemiBold)
    lbl.setFont(fnt)
    v.addWidget(lbl)
    v.addWidget(widget)
    return w

def _card(title: str, body: QWidget, stripe: str = "#2563EB") -> QFrame:
    outer = QFrame()
    outer.setObjectName("card")
    v = QVBoxLayout(outer)
    v.setContentsMargins(0, 0, 0, 0)
    v.setSpacing(0)
    hdr = QWidget()
    hdr.setFixedHeight(42)
    h = QHBoxLayout(hdr)
    h.setContentsMargins(14, 0, 14, 0)
    pill = QFrame()
    pill.setFixedSize(4, 18)
    pill.setStyleSheet(f"background: {stripe}; border-radius: 2px;")
    h.addWidget(pill)
    h.addSpacing(8)
    t = QLabel(title)
    t.setObjectName("card_title")
    h.addWidget(t)
    h.addStretch()
    v.addWidget(hdr)
    ls = QFrame()
    ls.setFrameShape(QFrame.Shape.HLine)
    ls.setStyleSheet("color: rgba(100, 130, 180, 0.12);")
    v.addWidget(ls)
    v.addWidget(body)
    return outer

class KPICard(QFrame):
    def __init__(self, tag: str, val: str = "—", obj: str = "kpi_accent", parent=None):
        super().__init__(parent)
        self.setObjectName("card2")
        v = QVBoxLayout(self)
        v.setContentsMargins(12, 10, 12, 10)
        v.setSpacing(2)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._t = QLabel(tag)
        self._t.setObjectName("tag")
        self._t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._v = QLabel(val)
        self._v.setObjectName(obj)
        self._v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        v.addWidget(self._t)
        v.addWidget(self._v)

    def set_val(self, v: str):
        self._v.setText(v)

class CipherForgeWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._theme = DARK
        self._is_dark = True
        self._worker = None
        self._analysis_worker = None
        self._analysis = None
        self._last_file = ""
        self._active_tier = "All"
        self._family_entries = []

        self.setWindowTitle("CipherForge — Smart Password Wordlist Studio")
        self.resize(1240, 840)
        self.setMinimumSize(980, 680)

        self._build()
        self._do_theme(DARK)

    def _build(self):
        root = QWidget()
        root.setObjectName("main_bg")
        rl = QHBoxLayout(root)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        rl.addWidget(self._sidebar())

        self._stack = QStackedWidget()
        self._stack.addWidget(self._pg_generator())
        self._stack.addWidget(self._pg_statistics())
        self._stack.addWidget(self._pg_entropy())
        self._stack.addWidget(self._pg_guide())

        rl.addWidget(self._stack, 1)
        self.setCentralWidget(root)
        self._nav(0)

    def _sidebar(self):
        sb = QFrame()
        sb.setObjectName("sidebar")
        sb.setFixedWidth(236)
        vl = QVBoxLayout(sb)
        vl.setContentsMargins(12, 18, 12, 14)
        vl.setSpacing(4)

        brow = QWidget()
        brow.setStyleSheet("background: transparent; border: none;")
        bl = QHBoxLayout(brow)
        bl.setContentsMargins(4, 0, 0, 0)
        bl.setSpacing(10)

        self._logo_lbl = QLabel()
        self._logo_lbl.setFixedSize(46, 46)
        self._logo_lbl.setStyleSheet("background: transparent; border: none;")
        self._load_brand_logo()
        bl.addWidget(self._logo_lbl)

        bcol = QWidget()
        bcol.setStyleSheet("background: transparent; border: none;")
        bv = QVBoxLayout(bcol)
        bv.setContentsMargins(0, 0, 0, 0)
        bv.setSpacing(1)
        t1 = QLabel("CipherForge")
        t1.setObjectName("h1")
        t1.setStyleSheet("background: transparent; font-size: 17px; font-weight: 700;")
        t2 = QLabel("Wordlist Studio v2.6")
        t2.setObjectName("muted")
        t2.setStyleSheet("background: transparent;")
        bv.addWidget(t1)
        bv.addWidget(t2)
        bl.addWidget(bcol)
        vl.addWidget(brow)

        vl.addSpacing(10)
        vl.addWidget(_sep())
        vl.addSpacing(8)

        self._nav_btns = []
        nav_items = [
            ("⚡  Generator Engine", 0),
            ("📊  Wordlist Analytics", 1),
            ("🔐  Entropy Inspector", 2),
            ("📖  Engine Guide", 3)
        ]
        for label, idx in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("nav_btn")
            btn.setFixedHeight(40)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _, i=idx: self._nav(i))
            vl.addWidget(btn)
            self._nav_btns.append(btn)

        vl.addSpacing(10)
        vl.addWidget(_sep())
        vl.addSpacing(10)

        tag = QLabel("APPEARANCE")
        tag.setObjectName("tag")
        tag.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vl.addWidget(tag)
        vl.addSpacing(4)

        trow = QHBoxLayout()
        trow.setSpacing(6)
        self._btn_dark = QPushButton("🌙 Dark")
        self._btn_light = QPushButton("☀️ Light")
        for b in (self._btn_dark, self._btn_light):
            b.setObjectName("theme_btn")
            b.setFixedHeight(30)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            trow.addWidget(b)

        self._btn_dark.clicked.connect(lambda: self._do_theme(DARK))
        self._btn_light.clicked.connect(lambda: self._do_theme(LIGHT))
        vl.addLayout(trow)

        vl.addStretch()

        folder_box = QFrame()
        folder_box.setObjectName("card2")
        fb_v = QVBoxLayout(folder_box)
        fb_v.setContentsMargins(10, 8, 10, 8)
        fb_v.setSpacing(4)
        
        fb_lbl = QLabel("📁 Output Directory:")
        fb_lbl.setStyleSheet("font-size: 10px; font-weight: 700; color: #64748B;")
        self._side_dir_lbl = QLabel("generated_wordlists/")
        self._side_dir_lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #38BDF8;")
        
        btn_open_out = QPushButton("Open Folder")
        btn_open_out.setObjectName("btn_ghost")
        btn_open_out.setFixedHeight(24)
        btn_open_out.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open_out.clicked.connect(self._open_folder)

        fb_v.addWidget(fb_lbl)
        fb_v.addWidget(self._side_dir_lbl)
        fb_v.addWidget(btn_open_out)
        vl.addWidget(folder_box)

        vl.addSpacing(4)
        vl.addWidget(_sep())
        vl.addSpacing(4)

        self._side_status = QLabel("● Engine Ready")
        self._side_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600;")
        self._side_words = QLabel("0 words generated")
        self._side_words.setObjectName("muted")
        vl.addWidget(self._side_status)
        vl.addWidget(self._side_words)
        return sb

    def _load_brand_logo(self):
        logo_png = os.path.join(ASSETS, "logo.png")
        logo_jpg = os.path.join(ASSETS, "logo.jpg")
        path = logo_png if os.path.exists(logo_png) else logo_jpg
        if os.path.exists(path):
            px = QPixmap(path).scaled(
                44, 44, Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._logo_lbl.setPixmap(px)
        else:
            self._logo_lbl.setText("⚡")
            self._logo_lbl.setStyleSheet("font-size: 28px; color: #2563EB;")

    def _nav(self, idx: int):
        self._stack.setCurrentIndex(idx)
        for i, btn in enumerate(self._nav_btns):
            btn.setProperty("nav_active", "1" if i == idx else "0")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _pg_generator(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        page = QWidget()
        vl = QVBoxLayout(page)
        vl.setContentsMargins(20, 16, 20, 20)
        vl.setSpacing(14)

        hrow = QHBoxLayout()
        hl = QLabel("⚡  Generator Engine")
        hl.setObjectName("h1")
        hrow.addWidget(hl)
        hrow.addStretch()

        btn_demo = QPushButton("✨ Fill Demo Details")
        btn_demo.setObjectName("btn_ghost")
        btn_demo.setFixedHeight(32)
        btn_demo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_demo.clicked.connect(self._fill_demo)
        hrow.addWidget(btn_demo)

        btn_clear = QPushButton("Clear Details")
        btn_clear.setObjectName("btn_ghost")
        btn_clear.setFixedHeight(32)
        btn_clear.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear.clicked.connect(self._clear_details)
        hrow.addWidget(btn_clear)

        vl.addLayout(hrow)

        self._inputs = {}
        pf = QWidget()
        pg = QGridLayout(pf)
        pg.setContentsMargins(14, 8, 14, 10)
        pg.setSpacing(12)

        self._inputs["name"] = QLineEdit()
        self._inputs["name"].setPlaceholderText("E.g. Aarav")
        pg.addWidget(_field("First Name *", self._inputs["name"]), 0, 0)

        self._inputs["last"] = QLineEdit()
        self._inputs["last"].setPlaceholderText("E.g. Sharma")
        pg.addWidget(_field("Last Name", self._inputs["last"]), 0, 1)

        self._inputs["year"] = QLineEdit()
        self._inputs["year"].setPlaceholderText("E.g. 1995")
        pg.addWidget(_field("Birth Year *", self._inputs["year"]), 1, 0)

        self._inputs["city"] = QLineEdit()
        self._inputs["city"].setPlaceholderText("E.g. Mumbai")
        pg.addWidget(_field("City / Location", self._inputs["city"]), 1, 1)

        self._inputs["pet"] = QLineEdit()
        self._inputs["pet"].setPlaceholderText("E.g. Bruno")
        pg.addWidget(_field("Pet Name", self._inputs["pet"]), 2, 0)

        self._inputs["color"] = QLineEdit()
        self._inputs["color"].setPlaceholderText("E.g. Blue")
        pg.addWidget(_field("Favorite Color", self._inputs["color"]), 2, 1)

        self._inputs["sport"] = QLineEdit()
        self._inputs["sport"].setPlaceholderText("E.g. Cricket")
        pg.addWidget(_field("Favorite Sport", self._inputs["sport"]), 3, 0)

        self._inputs["custom_phrases"] = QLineEdit()
        self._inputs["custom_phrases"].setPlaceholderText("E.g. Welcome@123 (comma-separated)")
        pg.addWidget(_field("Custom Passphrases / Keywords", self._inputs["custom_phrases"]), 3, 1)

        pg.setColumnStretch(0, 1)
        pg.setColumnStretch(1, 1)

        pw = QWidget()
        pv = QVBoxLayout(pw)
        pv.setContentsMargins(0, 0, 0, 0)
        pv.setSpacing(0)
        pv.addWidget(pf)
        vl.addWidget(_card("👤  Target Profile Attributes", pw, "#2563EB"))

        fam_card_body = QWidget()
        fam_v = QVBoxLayout(fam_card_body)
        fam_v.setContentsMargins(14, 8, 14, 12)
        fam_v.setSpacing(10)

        fam_desc = QLabel("Add family members (spouse, children, siblings) to enrich permutations:")
        fam_desc.setObjectName("muted")
        fam_v.addWidget(fam_desc)

        f_in_row = QHBoxLayout()
        f_in_row.setSpacing(8)
        f_in_row.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # DropdownComboBox: expands strictly below the field, matching width, leaving field visible above
        self._combo_relation = DropdownComboBox()
        combo_view = QListView()
        self._combo_relation.setView(combo_view)

        self._combo_relation.addItems(RELATIONS)
        self._combo_relation.setMaxVisibleItems(len(RELATIONS))
        self._combo_relation.setFixedWidth(135)
        self._combo_relation.setFixedHeight(34)

        self._in_fam_name = QLineEdit()
        self._in_fam_name.setPlaceholderText("E.g. Priya")
        self._in_fam_name.setFixedHeight(34)

        btn_add_fam = QPushButton("＋ Add Member")
        btn_add_fam.setObjectName("btn_secondary")
        btn_add_fam.setFixedHeight(34)
        btn_add_fam.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add_fam.clicked.connect(self._add_family_member)

        f_in_row.addWidget(self._combo_relation)
        f_in_row.addWidget(self._in_fam_name, 1)
        f_in_row.addWidget(btn_add_fam)
        fam_v.addLayout(f_in_row)

        self._fam_badge_box = QWidget()
        self._fam_badge_layout = QHBoxLayout(self._fam_badge_box)
        self._fam_badge_layout.setContentsMargins(0, 0, 0, 0)
        self._fam_badge_layout.setSpacing(6)
        self._fam_badge_layout.addStretch()
        fam_v.addWidget(self._fam_badge_box)

        # Output Filename in Card 2
        self._inputs["output"] = QLineEdit()
        self._inputs["output"].setPlaceholderText("E.g. aarav_wordlist.txt")
        self._inputs["output"].setFixedHeight(34)
        fam_v.addWidget(_field("💾 Output Wordlist Filename (saved in generated_wordlists/)", self._inputs["output"]))

        vl.addWidget(_card("👥  Family Members & Output File Configuration", fam_card_body, "#8B5CF6"))

        opts_body = QWidget()
        og = QGridLayout(opts_body)
        og.setContentsMargins(14, 8, 14, 12)
        og.setSpacing(12)

        self._in_min = QLineEdit("6")
        self._in_min.setFixedHeight(34)
        self._in_max = QLineEdit("20")
        self._in_max.setFixedHeight(34)

        og.addWidget(_field("Min Length", self._in_min), 0, 0)
        og.addWidget(_field("Max Length", self._in_max), 0, 1)

        leet_w = QWidget()
        lv = QVBoxLayout(leet_w)
        lv.setContentsMargins(0, 0, 0, 0)
        lv.setSpacing(4)
        self._leet_lbl = QLabel("Leet Depth: 80 variants / root")
        self._leet_lbl.setObjectName("muted")
        self._leet_lbl.setStyleSheet("font-size: 11px; font-weight: 600;")
        self._leet_s = QSlider(Qt.Orientation.Horizontal)
        self._leet_s.setRange(20, 200)
        self._leet_s.setValue(80)
        self._leet_s.setSingleStep(10)
        self._leet_s.valueChanged.connect(lambda v: self._leet_lbl.setText(f"Leet Depth: {v} variants / root"))
        lv.addWidget(self._leet_lbl)
        lv.addWidget(self._leet_s)
        og.addWidget(leet_w, 0, 2)

        og.setColumnStretch(0, 1)
        og.setColumnStretch(1, 1)
        og.setColumnStretch(2, 2)
        vl.addWidget(_card("⚙️  Synthesis Boundaries", opts_body, "#10B981"))

        # Card 4: Execution Control
        af = QWidget()
        av = QVBoxLayout(af)
        av.setContentsMargins(14, 8, 14, 10)
        av.setSpacing(10)

        brow2 = QHBoxLayout()
        brow2.setSpacing(10)

        self._btn_gen = QPushButton("⚡  Generate Wordlist")
        self._btn_gen.setObjectName("btn_primary")
        self._btn_gen.setFixedHeight(46)
        self._btn_gen.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_gen.clicked.connect(self._start_generation)

        self._btn_est = QPushButton("🔢  Estimate Count")
        self._btn_est.setObjectName("btn_secondary")
        self._btn_est.setFixedHeight(46)
        self._btn_est.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_est.clicked.connect(self._estimate)

        # Stop button with clean, minimal red circular UI symbol (no colorful emoji)
        self._btn_stop = QPushButton("●  Stop")
        self._btn_stop.setObjectName("btn_danger")
        self._btn_stop.setFixedHeight(46)
        self._btn_stop.setEnabled(False)
        self._btn_stop.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_stop.clicked.connect(self._stop)

        brow2.addWidget(self._btn_gen, 3)
        brow2.addWidget(self._btn_est, 2)
        brow2.addWidget(self._btn_stop, 1)
        av.addLayout(brow2)

        self._pbar = QProgressBar()
        self._pbar.setRange(0, 100)
        self._pbar.setValue(0)
        self._pbar.setTextVisible(False)
        self._pbar.setFixedHeight(8)
        av.addWidget(self._pbar)

        srow = QHBoxLayout()
        self._status_lbl = QLabel("Ready to generate.")
        self._status_lbl.setObjectName("muted")
        srow.addWidget(self._status_lbl)
        srow.addStretch()
        av.addLayout(srow)

        vl.addWidget(_card("🚀  Execution Control", af, "#F59E0B"))

        # Card 5: Telemetry Logs with 🔴 🟡 🟢 dots, prompt, and Clear Logs button
        lf = QWidget()
        lv2 = QVBoxLayout(lf)
        lv2.setContentsMargins(14, 8, 14, 12)
        lv2.setSpacing(8)

        term_hdr = QWidget()
        term_hl = QHBoxLayout(term_hdr)
        term_hl.setContentsMargins(0, 0, 0, 0)
        term_hl.setSpacing(8)

        dots_w = QWidget()
        dl = QHBoxLayout(dots_w)
        dl.setContentsMargins(0, 0, 0, 0)
        dl.setSpacing(6)
        for dot_c in ["#EF4444", "#F59E0B", "#10B981"]:
            dot = QFrame()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background-color: {dot_c}; border-radius: 5px;")
            dl.addWidget(dot)
        term_hl.addWidget(dots_w)

        term_prompt = QLabel("cipherforge@engine:~$")
        term_prompt.setStyleSheet("font-family: 'Cascadia Code', Consolas, monospace; font-size: 11px; font-weight: 700; color: #38BDF8;")
        term_hl.addWidget(term_prompt)

        term_hl.addStretch()

        btn_clear_log = QPushButton("Clear Logs")
        btn_clear_log.setObjectName("terminal_btn")
        btn_clear_log.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_clear_log.clicked.connect(self._clear_console)
        term_hl.addWidget(btn_clear_log)

        lv2.addWidget(term_hdr)

        self._console = QPlainTextEdit()
        self._console.setObjectName("console")
        self._console.setReadOnly(True)
        self._console.setFixedHeight(160)
        lv2.addWidget(self._console)

        krow = QHBoxLayout()
        krow.setSpacing(8)
        self._kw = KPICard("WORDS GENERATED", "0", "kpi_accent")
        self._kt = KPICard("ELAPSED TIME", "0.00s", "kpi_success")
        self._ks = KPICard("RATE (WORDS/SEC)", "0", "kpi_purple")
        self._kf = KPICard("OUTPUT FILE", "—", "kpi_warn")
        for k in (self._kw, self._kt, self._ks, self._kf):
            krow.addWidget(k)
        lv2.addLayout(krow)

        vl.addWidget(_card("📋  Telemetry Logs", lf, "#8B5CF6"))

        scroll.setWidget(page)
        return scroll

    def _clear_console(self):
        self._console.clear()
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._console.appendPlainText(f"[{ts}] [SYS] Terminal initialized. Engine standby.")

    def _add_family_member(self):
        rel = self._combo_relation.currentText()
        name = self._in_fam_name.text().strip()
        if not name:
            return

        item = f"{rel}: {name}"
        if item in self._family_entries:
            return

        self._family_entries.append(item)
        self._in_fam_name.clear()
        self._refresh_family_badges()

    def _remove_family_member(self, item: str):
        if item in self._family_entries:
            self._family_entries.remove(item)
            self._refresh_family_badges()

    def _refresh_family_badges(self):
        while self._fam_badge_layout.count():
            w = self._fam_badge_layout.takeAt(0).widget()
            if w:
                w.deleteLater()

        for item in self._family_entries:
            badge = QFrame()
            badge.setObjectName("card2")
            b_l = QHBoxLayout(badge)
            b_l.setContentsMargins(8, 4, 8, 4)
            b_l.setSpacing(6)

            lbl = QLabel(item)
            lbl.setStyleSheet("font-size: 11px; font-weight: 600; color: #38BDF8;")
            b_l.addWidget(lbl)

            btn_del = QPushButton("✕")
            btn_del.setFixedSize(16, 16)
            btn_del.setStyleSheet("border: none; color: #EF4444; font-weight: bold; font-size: 11px;")
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.clicked.connect(lambda _, it=item: self._remove_family_member(it))
            b_l.addWidget(btn_del)

            self._fam_badge_layout.addWidget(badge)

        self._fam_badge_layout.addStretch()

    def _pg_statistics(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        page = QWidget()
        vl = QVBoxLayout(page)
        vl.setContentsMargins(20, 16, 20, 20)
        vl.setSpacing(14)

        hrow = QHBoxLayout()
        hl = QLabel("📊  Wordlist Analytics")
        hl.setObjectName("h1")
        hrow.addWidget(hl)
        hrow.addStretch()

        bimp = QPushButton("📂  Analyze External Wordlist (.txt)")
        bimp.setObjectName("btn_secondary")
        bimp.setFixedHeight(34)
        bimp.setMinimumWidth(230)
        bimp.setCursor(Qt.CursorShape.PointingHandCursor)
        bimp.clicked.connect(self._import_file)
        hrow.addWidget(bimp)
        vl.addLayout(hrow)

        krow = QHBoxLayout()
        krow.setSpacing(10)
        self._sk_total = KPICard("TOTAL WORDS", "—", "kpi_accent")
        self._sk_len = KPICard("AVG LENGTH", "—", "kpi_success")
        self._sk_ent = KPICard("AVG ENTROPY (bits)", "—", "kpi_purple")
        self._sk_strong = KPICard("HIGH STRENGTH COUNT", "—", "kpi_warn")
        for k in (self._sk_total, self._sk_len, self._sk_ent, self._sk_strong):
            k.setFixedHeight(84)
            krow.addWidget(k)
        vl.addLayout(krow)

        crow = QHBoxLayout()
        crow.setSpacing(12)
        self._c_len = BarChart()
        self._c_len.setMinimumHeight(220)
        crow.addWidget(_card("📏  Word Length Distribution", self._c_len, "#2563EB"))

        self._c_char = BarChart()
        self._c_char.setMinimumHeight(220)
        crow.addWidget(_card("🔤  Top Character Frequency", self._c_char, "#10B981"))
        vl.addLayout(crow)

        prow = QHBoxLayout()
        prow.setSpacing(12)
        self._c_pat = DonutChart()
        self._c_pat.setMinimumHeight(220)
        prow.addWidget(_card("🎯  Pattern Composition", self._c_pat, "#8B5CF6"))

        self._c_tier = BarChart()
        self._c_tier.setMinimumHeight(220)
        prow.addWidget(_card("🔒  Strength Tier Breakdown", self._c_tier, "#F59E0B"))
        vl.addLayout(prow)

        scroll.setWidget(page)
        self._all_charts = [self._c_len, self._c_char, self._c_pat, self._c_tier]
        return scroll

    def _pg_entropy(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        page = QWidget()
        vl = QVBoxLayout(page)
        vl.setContentsMargins(20, 16, 20, 20)
        vl.setSpacing(14)

        hl = QLabel("🔐  Entropy Inspector & Security Analysis")
        hl.setObjectName("h1")
        vl.addWidget(hl)

        self._toast_banner = QFrame()
        self._toast_banner.setObjectName("card2")
        self._toast_banner.setVisible(False)
        tb_l = QHBoxLayout(self._toast_banner)
        tb_l.setContentsMargins(16, 8, 16, 8)
        tb_l.setSpacing(12)
        tb_l.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self._toast_lbl = QLabel()
        self._toast_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #10B981;")
        self._toast_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        tb_l.addWidget(self._toast_lbl, 1)

        btn_toast_open = QPushButton("Open Directory")
        btn_toast_open.setObjectName("btn_ghost")
        btn_toast_open.setFixedHeight(30)
        btn_toast_open.setMinimumWidth(125)
        btn_toast_open.setStyleSheet("padding: 5px 16px; font-size: 11px; font-weight: 600; text-align: center;")
        btn_toast_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_toast_open.clicked.connect(self._open_folder)
        tb_l.addWidget(btn_toast_open)

        btn_toast_close = QPushButton("✕")
        btn_toast_close.setFixedSize(28, 28)
        btn_toast_close.setObjectName("btn_ghost")
        btn_toast_close.setStyleSheet("border-radius: 6px; color: #94A3B8; font-weight: bold; font-size: 12px; text-align: center; padding: 0px;")
        btn_toast_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_toast_close.clicked.connect(lambda: self._toast_banner.setVisible(False))
        tb_l.addWidget(btn_toast_close)

        vl.addWidget(self._toast_banner)

        tf = QWidget()
        tl = QHBoxLayout(tf)
        tl.setContentsMargins(14, 10, 14, 12)
        tl.setSpacing(10)

        self._live_in = QLineEdit()
        self._live_in.setPlaceholderText("E.g. Aarav@1995")
        self._live_in.setFixedHeight(38)
        self._live_in.textChanged.connect(self._live_test)
        tl.addWidget(self._live_in, 1)

        self._live_res = QLabel("Entropy: —")
        self._live_res.setFixedWidth(270)
        self._live_res.setFixedHeight(38)
        self._live_res.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._live_res.setStyleSheet("border: 1px solid #1E293B; border-radius: 6px; font-size: 13px; font-weight: 700; color: #94A3B8; padding: 0 10px;")
        tl.addWidget(self._live_res)
        vl.addWidget(_card("🧪  Real-Time Password Strength Tester", tf, "#EF4444"))

        tbf = QWidget()
        tbv = QVBoxLayout(tbf)
        tbv.setContentsMargins(14, 8, 14, 10)
        tbv.setSpacing(8)

        frow = QHBoxLayout()
        frow.setSpacing(6)
        fl = QLabel("Filter:")
        fl.setObjectName("muted")
        frow.addWidget(fl)

        self._tier_btns = []
        for tn in ["All", "Weak", "Fair", "Strong", "Excellent"]:
            b = QPushButton(tn)
            b.setObjectName("tag_btn")
            b.setFixedHeight(28)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _, n=tn: self._filter(n))
            frow.addWidget(b)
            self._tier_btns.append(b)

        frow.addStretch()

        self._btn_export = QPushButton("💾  Export Selected Tier")
        self._btn_export.setObjectName("btn_secondary")
        self._btn_export.setFixedHeight(32)
        self._btn_export.setMinimumWidth(170)
        self._btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_export.clicked.connect(self._export)
        frow.addWidget(self._btn_export)
        tbv.addLayout(frow)

        leg = QHBoxLayout()
        leg.setSpacing(16)
        for col, desc in [("#EF4444", "Weak < 2.0 bits"), ("#F59E0B", "Fair 2.0–3.0 bits"),
                         ("#10B981", "Strong 3.0–3.8 bits"), ("#8B5CF6", "Excellent > 3.8 bits")]:
            l = QLabel(f"● {desc}")
            l.setStyleSheet(f"color: {col}; font-size: 10px; font-weight: 600;")
            leg.addWidget(l)
        leg.addStretch()
        tbv.addLayout(leg)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["#", "Password", "Entropy (bits)", "Strength Tier"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setMinimumHeight(380)
        tbv.addWidget(self._table)

        vl.addWidget(_card("🔐  Password Entropy Ranking Matrix", tbf, "#8B5CF6"))

        scroll.setWidget(page)
        return scroll

    def _pg_guide(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        page = QWidget()
        vl = QVBoxLayout(page)
        vl.setContentsMargins(20, 16, 20, 20)
        vl.setSpacing(14)

        hl = QLabel("📖  Engine Guide")
        hl.setObjectName("h1")
        vl.addWidget(hl)

        top_banner = QFrame()
        top_banner.setObjectName("card2")
        tb_lay = QVBoxLayout(top_banner)
        tb_lay.setContentsMargins(16, 14, 16, 14)
        tb_lay.setSpacing(4)
        tb_title = QLabel("⚡ CipherForge 3-Stage Synthesis Architecture")
        tb_title.setStyleSheet("font-size: 13px; font-weight: 700; color: #38BDF8;")
        tb_body = QLabel("CipherForge uses targeted psychological anchor profiling to generate high-probability credential dictionaries for security auditing, authorized penetration testing, and password resilience benchmarking.")
        tb_body.setWordWrap(True)
        tb_body.setStyleSheet("font-size: 11px; color: #94A3B8; line-height: 1.4;")
        tb_lay.addWidget(tb_title)
        tb_lay.addWidget(tb_body)
        vl.addWidget(top_banner)

        stages = [
            ("Stage 1: Seed Matrix & Semantic Roots", "#2563EB", [
                "Primary Tokens: First name, last name, birth year, pet, city, color, sport.",
                "Family Semantic Links: Cross-connects spouse, child, sibling anchors.",
                "Custom Phrases: Inserts known passphrases, keywords, and space-stripped variants.",
                "High-Probability Combos: Name+Year, Name+Last, Pet+Year, City+Year.",
                "Special Separators: Name + Special (!, @, #, $, %, &) + Birth Year."
            ]),
            ("Stage 2: Mutation & Leetspeak Matrix", "#10B981", [
                "5 Case Variants: lowercase, UPPERCASE, Capitalized, aLtErNaTiNg, ALtErNaTiNg.",
                "Smart Leet Substitutions: a→@,4 | e→3 | i→1,! | o→0 | s→$,5 | t→7,+ | b→8 | g→9 | l→1 | z→2.",
                "Bounded Permutations: Controls combinatorial growth via Leet Depth slider (20–200 variants/root).",
                "Non-alphanumeric preservation: Preserves digits and special characters during leet transforms."
            ]),
            ("Stage 3: Cartesian Affix Synthesis", "#F59E0B", [
                "System Prefixes: admin_, user_, root_, hack_, pass_, secret_ (plus plain root).",
                "22 High-Frequency Suffixes: 123, 007, 69, 420, 2024, 2025, 2026, !, @, #, $, %, &, *, ?, .",
                "Dynamic Year Injections: Appends target's full 4-digit birth year and 2-digit abbreviation.",
                "Strict Length Boundary: Discards all candidates outside [Min Length, Max Length].",
                "Deduplication: Employs Python set hash tables for instantaneous duplicate elimination."
            ]),
            ("Stage 4: Shannon Entropy & Resilience Rating", "#8B5CF6", [
                "Mathematical Formula: Shannon Entropy H = -Σ p(c) · log₂(p(c)) [bits/character].",
                "Weak Tier (< 2.0 bits): Low character variety; cracked in seconds by brute-force.",
                "Fair Tier (2.0–3.0 bits): Standard lowercase alphanumeric combinations.",
                "Strong Tier (3.0–3.8 bits): High complexity mixed alphanumeric with symbols.",
                "Excellent Tier (> 3.8 bits): Maximum bit entropy; optimal resistance to dictionary attacks."
            ]),
        ]

        grid = QGridLayout()
        grid.setSpacing(12)

        for idx, (title, color, bullets) in enumerate(stages):
            card_w = QWidget()
            cv = QVBoxLayout(card_w)
            cv.setContentsMargins(14, 12, 14, 12)
            cv.setSpacing(6)

            for b in bullets:
                b_lbl = QLabel(f"•  {b}")
                b_lbl.setWordWrap(True)
                b_lbl.setStyleSheet("font-size: 11px; line-height: 1.4;")
                cv.addWidget(b_lbl)

            grid.addWidget(_card(title, card_w, color), idx // 2, idx % 2)

        vl.addLayout(grid)

        tip_card = QFrame()
        tip_card.setObjectName("card2")
        tv = QVBoxLayout(tip_card)
        tv.setContentsMargins(16, 14, 16, 14)
        tv.setSpacing(4)

        t_h = QLabel("💡  Security Auditor's Cheat Sheet:")
        t_h.setStyleSheet("font-weight: 700; color: #10B981; font-size: 12px;")
        t_b = QLabel("1. Focus length boundaries between 8 and 16 characters for enterprise compliance audits.\n2. Add spouse and child names to test social engineering password patterns.\n3. Use 'Export Selected Tier' to extract only Strong & Excellent candidates for targeted hash verification.")
        t_b.setWordWrap(True)
        t_b.setStyleSheet("font-size: 11px; color: #94A3B8; line-height: 1.5;")

        tv.addWidget(t_h)
        tv.addWidget(t_b)
        vl.addWidget(tip_card)

        scroll.setWidget(page)
        return scroll

    def _fill_demo(self):
        first = random.choice(INDIAN_FIRST_NAMES)
        last = random.choice(INDIAN_LAST_NAMES)
        pet = random.choice(INDIAN_PETS)
        city = random.choice(INDIAN_CITIES)
        color = random.choice(INDIAN_COLORS)
        sport = random.choice(INDIAN_SPORTS)
        year = str(random.randint(1975, 2006))

        self._inputs["name"].setText(first)
        self._inputs["last"].setText(last)
        self._inputs["year"].setText(year)
        self._inputs["pet"].setText(pet)
        self._inputs["city"].setText(city)
        self._inputs["color"].setText(color)
        self._inputs["sport"].setText(sport)
        self._inputs["custom_phrases"].setText(f"Welcome@{year}")
        self._inputs["output"].setText(f"{first.lower()}_wordlist.txt")

        self._family_entries = []
        rel_choice = random.choice(["Spouse", "Sibling", "Child"])
        fam_name = random.choice([n for n in INDIAN_FIRST_NAMES if n != first])
        self._family_entries.append(f"{rel_choice}: {fam_name}")
        self._refresh_family_badges()

        self._log(f"[DEMO] Loaded profile: {first} {last} (DOB: {year}, {city})")

    def _clear_details(self):
        for e in self._inputs.values():
            e.clear()
        self._family_entries.clear()
        self._refresh_family_badges()
        self._in_min.setText("6")
        self._in_max.setText("20")
        self._leet_s.setValue(80)
        self._pbar.setValue(0)
        self._status_lbl.setText("Ready to generate.")
        self._kw.set_val("0")
        self._kt.set_val("0.00s")
        self._ks.set_val("0")
        self._kf.set_val("—")
        self._side_status.setText("● Engine Ready")
        self._side_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600;")
        self._side_words.setText("0 words generated")
        self._log("[RESET] Cleared all profile fields and configuration parameters.")

    def _collect_profile(self) -> dict | None:
        data = {k: e.text().strip() for k, e in self._inputs.items()}
        if not data.get("name"):
            self._log("[ERR] First Name is required.")
            return None
        year = data.get("year", "")
        if not year or not year.isdigit() or len(year) != 4:
            self._log("[ERR] Birth Year must be exactly 4 digits (e.g. 1995).")
            return None

        try:
            mn = int(self._in_min.text().strip() or DEFAULT_MIN_LEN)
            mx = int(self._in_max.text().strip() or DEFAULT_MAX_LEN)
            if mn > mx:
                self._log("[ERR] Min Length cannot exceed Max Length.")
                return None
            data["min_len"] = mn
            data["max_len"] = mx
        except ValueError:
            self._log("[ERR] Min/Max length must be integers.")
            return None

        fam_names = []
        for entry in self._family_entries:
            if ":" in entry:
                fam_names.append(entry.split(":", 1)[1].strip())
            else:
                fam_names.append(entry.strip())
        data["family_members"] = fam_names

        cust_str = self._inputs.get("custom_phrases", QLineEdit()).text().strip()
        if cust_str:
            phrases = [p.strip() for p in cust_str.split(",") if p.strip()]
            data["custom_phrases"] = phrases
        else:
            data["custom_phrases"] = []

        data["leet_max"] = self._leet_s.value()
        return data

    def _estimate(self):
        p = self._collect_profile()
        if not p:
            return
        est = estimate_count(p, p["leet_max"], p["min_len"], p["max_len"])
        bases = build_base_candidates(p)

        self._kw.set_val(f"~{est:,}")
        self._kf.set_val("Forecast")
        self._status_lbl.setText(f"Estimated Candidates: ~{est:,} words (within {p['min_len']}–{p['max_len']} chars)")
        self._side_words.setText(f"~{est:,} est. words")
        self._log(f"[FORECAST] Matrix: {len(bases)} structural roots -> ~{est:,} unique words estimate.")

    def _start_generation(self):
        p = self._collect_profile()
        if not p:
            return

        self._console.clear()
        self._log(f"[START] Starting CipherForge synthesis pipeline for target: '{p['name']}'...")

        self._btn_gen.setEnabled(False)
        self._btn_est.setEnabled(False)
        self._btn_stop.setEnabled(True)
        self._pbar.setValue(0)
        self._status_lbl.setText("Synthesizing wordlist combinations...")
        self._side_status.setText("● Synthesizing...")
        self._side_status.setStyleSheet("color: #F59E0B; font-size: 11px; font-weight: 600;")

        out_name = p.get("output") or None
        self._worker = GenerationWorker(p, p["leet_max"], p["min_len"], p["max_len"], out_name)
        self._worker.progress.connect(self._on_progress)
        self._worker.complete.connect(self._on_complete)
        self._worker.start()

    def _stop(self):
        if self._worker:
            self._worker.stop()
        self._status_lbl.setText("Aborting...")
        self._log("[ABORT] Stop signal dispatched to worker thread.")

    def _on_progress(self, p: dict):
        pct = float(p.get("pct", 0))
        self._pbar.setValue(int(pct * 100))
        self._status_lbl.setText(p.get("detail", ""))
        self._log(f"  > {p.get('detail', '')}")

    def _on_complete(self, res: dict):
        self._btn_gen.setEnabled(True)
        self._btn_est.setEnabled(True)
        self._btn_stop.setEnabled(False)
        self._worker = None

        if res["count"] == 0:
            self._pbar.setValue(0)
            self._status_lbl.setText("No words matched the length filters.")
            self._side_status.setText("● Engine Ready")
            self._side_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600;")
            self._log("[WARN] Zero words matched the length boundaries.")
            return

        self._pbar.setValue(100)
        self._last_file = res.get("file", "")
        count_str = f"{res['count']:,}"

        self._kw.set_val(count_str)
        self._kt.set_val(f"{res['elapsed']:.2f}s")
        self._ks.set_val(f"{res['rate']:,}/s")
        self._kf.set_val(os.path.basename(self._last_file) if self._last_file else "done")

        self._side_status.setText("● Complete ✓")
        self._side_status.setStyleSheet("color: #10B981; font-size: 11px; font-weight: 600;")
        self._side_words.setText(f"{count_str} words ready")
        self._status_lbl.setText(f"Done — Generated {count_str} words in {res['elapsed']:.2f}s")

        self._log(f"[SUCCESS] Generated {count_str} words in {res['elapsed']:.2f}s ({res['rate']:,} words/sec)")
        if self._last_file:
            self._log(f"  Output saved: {self._last_file}")

        wordlist = res.get("wordlist", set())
        if wordlist:
            self._analysis = analyze_wordlist(wordlist)
            self._render_stats(self._analysis)

    def _log(self, text: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self._console.appendPlainText(f"[{ts}] {text}")

    def _open_folder(self):
        target_dir = get_output_dir()
        try:
            if sys.platform == "win32":
                os.startfile(target_dir)
            else:
                import subprocess
                subprocess.Popen(["xdg-open" if sys.platform != "darwin" else "open", target_dir])
            self._log(f"[SYS] Opened output directory: {target_dir}")
        except Exception as e:
            self._log(f"[ERR] Could not open folder: {e}")

    def _import_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Wordlist File", "", "Text Files (*.txt);;All Files (*)")
        if not path:
            return

        self._log(f"[IMPORT] Loading and analyzing: {os.path.basename(path)}...")
        self._analysis_worker = FileAnalysisWorker(path)
        self._analysis_worker.finished.connect(self._on_import_finished)
        self._analysis_worker.start()

    def _on_import_finished(self, analysis, filepath: str, error: str):
        if error:
            self._log(f"[ERR] Failed to analyze file: {error}")
            return

        self._analysis = analysis
        self._render_stats(analysis)
        self._log(f"[ANALYSIS] Successfully processed {analysis.total_words:,} words from: {os.path.basename(filepath)}")

    def _render_stats(self, a):
        self._sk_total.set_val(f"{a.total_words:,}")
        self._sk_len.set_val(f"{a.avg_length:.1f} chars")
        self._sk_ent.set_val(f"{a.avg_entropy:.2f}")
        strong = a.strength_tiers.get("Strong", 0) + a.strength_tiers.get("Excellent", 0)
        self._sk_strong.set_val(f"{strong:,}")

        t = self._theme
        self._c_len.set_data([(str(k), v) for k, v in a.length_distribution.items()], t["accent"])
        self._c_char.set_data(list(a.char_frequency.items())[:14], t["success"])
        self._c_tier.set_data(list(a.strength_tiers.items()), t["purple"])
        self._c_pat.set_data(a.pattern_breakdown)

        self._fill_table(a.entropy_scores, "All")

    def _fill_table(self, scored: list, tier: str = "All"):
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(0)
        rows = scored
        if tier != "All":
            rows = [(w, e) for w, e in rows if strength_tier(e) == tier]

        limit = min(len(rows), 10000)
        self._table.setRowCount(limit)
        for i, (word, score) in enumerate(rows[:limit]):
            tr = strength_tier(score)
            col = {"Weak": "#EF4444", "Fair": "#F59E0B", "Strong": "#10B981", "Excellent": "#8B5CF6"}.get(tr, "#94A3B8")
            for c, txt in enumerate([str(i + 1), word, f"{score:.4f}", tr]):
                item = QTableWidgetItem(txt)
                item.setTextAlignment(int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft))
                if c == 3:
                    item.setForeground(QColor(col))
                self._table.setItem(i, c, item)
        self._table.setUpdatesEnabled(True)

    def _live_test(self, text: str):
        if not text:
            self._live_res.setText("Entropy: —")
            return
        score = shannon_entropy(text)
        tier = strength_tier(score)
        col = {"Weak": "#EF4444", "Fair": "#F59E0B", "Strong": "#10B981", "Excellent": "#8B5CF6"}.get(tier, "#2563EB")
        self._live_res.setText(f"  {score:.3f} bits  |  {tier}  ")
        self._live_res.setStyleSheet(f"color: {col}; font-size: 13px; font-weight: 700; border: 1.5px solid {col}; border-radius: 6px; padding: 0 10px; background: transparent;")

    def _filter(self, tier: str):
        self._active_tier = tier
        for btn in self._tier_btns:
            btn.setProperty("tag_active", "1" if btn.text() == tier else "0")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        if self._analysis:
            self._fill_table(self._analysis.entropy_scores, tier)

    def _export(self):
        if not self._analysis:
            self._log("[WARN] No wordlist available to export.")
            self._toast_lbl.setText("Warning: No wordlist available to export. Generate or load a wordlist first.")
            self._toast_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #F59E0B;")
            self._toast_banner.setStyleSheet("QFrame#card2 { background-color: rgba(245, 158, 11, 0.12); border: 1.5px solid #F59E0B; border-radius: 8px; }")
            self._toast_banner.setVisible(True)
            QTimer.singleShot(6000, lambda: self._toast_banner.setVisible(False))
            return

        tier = self._active_tier
        rows = self._analysis.entropy_scores
        if tier != "All":
            rows = [(w, e) for w, e in rows if strength_tier(e) == tier]
        if not rows:
            self._log(f"[WARN] No words match tier '{tier}'.")
            self._toast_lbl.setText(f"Warning: No words match the '{tier}' tier.")
            self._toast_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #F59E0B;")
            self._toast_banner.setStyleSheet("QFrame#card2 { background-color: rgba(245, 158, 11, 0.12); border: 1.5px solid #F59E0B; border-radius: 8px; }")
            self._toast_banner.setVisible(True)
            QTimer.singleShot(6000, lambda: self._toast_banner.setVisible(False))
            return

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        out_dir = get_output_dir()
        name = os.path.join(out_dir, f"cipherforge_{tier.lower()}_{ts}.txt")
        try:
            with open(name, "w", encoding="utf-8") as f:
                for w, _ in rows:
                    f.write(w + "\n")
            self._log(f"[EXPORT] Successfully exported {len(rows):,} words to: {os.path.abspath(name)}")
            self._toast_lbl.setText(f"✓ Export Complete: {len(rows):,} '{tier}' words saved to {os.path.basename(name)}")
            self._toast_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #10B981;")
            self._toast_banner.setStyleSheet("QFrame#card2 { background-color: rgba(16, 185, 129, 0.12); border: 1.5px solid #10B981; border-radius: 8px; }")
            self._toast_banner.setVisible(True)
            QTimer.singleShot(7000, lambda: self._toast_banner.setVisible(False))
        except Exception as e:
            self._log(f"[ERR] Export failed: {e}")
            self._toast_lbl.setText(f"Error: Export failed - {e}")
            self._toast_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #EF4444;")
            self._toast_banner.setStyleSheet("QFrame#card2 { background-color: rgba(239, 68, 68, 0.12); border: 1.5px solid #EF4444; border-radius: 8px; }")
            self._toast_banner.setVisible(True)
            QTimer.singleShot(6000, lambda: self._toast_banner.setVisible(False))

    def _do_theme(self, t: dict):
        self._theme = t
        self._is_dark = (t is DARK)

        pal = QApplication.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(t["app_bg"]))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(t["text"]))
        pal.setColor(QPalette.ColorRole.Base, QColor(t["input_bg"]))
        pal.setColor(QPalette.ColorRole.Text, QColor(t["text"]))
        pal.setColor(QPalette.ColorRole.Button, QColor(t["card_bg2"]))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(t["text"]))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(t["accent"]))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
        QApplication.setPalette(pal)

        QApplication.instance().setStyleSheet(_qss(t))

        # Re-apply scoped styling to dropdown popup container for clean single opaque menu
        if hasattr(self, "_combo_relation"):
            container = self._combo_relation.view().parentWidget()
            if container:
                container.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
                container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                container.setFrameShape(QFrame.Shape.NoFrame)
                container.setLineWidth(0)
                container.setStyleSheet(f"""
                    QFrame {{
                        background: transparent;
                        border: none;
                        padding: 0px;
                        margin: 0px;
                    }}
                    QListView {{
                        background-color: {t['card_bg']};
                        color: {t['text']};
                        border: 1.5px solid {t['border2']};
                        border-radius: 8px;
                        padding: 4px;
                        outline: 0px;
                        selection-background-color: {t['accent']};
                        selection-color: #FFFFFF;
                    }}
                    QListView::item {{
                        padding: 6px 10px;
                        border-radius: 4px;
                        min-height: 22px;
                        color: {t['text']};
                        background-color: transparent;
                    }}
                    QListView::item:hover {{
                        background-color: {t['nav_hover']};
                        color: {t['text']};
                    }}
                    QListView::item:selected {{
                        background-color: {t['accent']};
                        color: #FFFFFF;
                    }}
                """)

        # Precisely style vertical scrollbar of console: no white track, only blue thumb
        if hasattr(self, "_console"):
            vsb = self._console.verticalScrollBar()
            vsb.setStyleSheet(f"""
                QScrollBar:vertical {{
                    background: {t['console_bg']};
                    background-color: {t['console_bg']};
                    width: 6px;
                    margin: 0px;
                    border: none;
                }}
                QScrollBar::handle:vertical {{
                    background: {t['accent']};
                    border-radius: 3px;
                    min-height: 24px;
                }}
                QScrollBar::handle:vertical:hover {{
                    background: {t['accent_glow']};
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
                QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                    background: {t['console_bg']};
                    background-color: {t['console_bg']};
                    border: none;
                    height: 0px;
                    width: 0px;
                }}
            """)

        for c in getattr(self, "_all_charts", []):
            if hasattr(c, "apply_theme"):
                c.apply_theme(t)
        if hasattr(self, "_c_pat"):
            self._c_pat.apply_theme(t)

        self._btn_dark.setProperty("theme_active", "1" if self._is_dark else "0")
        self._btn_light.setProperty("theme_active", "0" if self._is_dark else "1")
        for b in (self._btn_dark, self._btn_light):
            b.style().unpolish(b)
            b.style().polish(b)


def launch_gui():
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    win = CipherForgeWindow()
    win.show()
    sys.exit(app.exec())
