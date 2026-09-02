#!/usr/bin/env python3
"""
wordgen_gui.py — CipherForge GUI Entry Point
Launch with: python wordgen_gui.py
"""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from cipherforge.gui import CipherForgeApp

if __name__ == "__main__":
    app = CipherForgeApp()
    app.mainloop()
