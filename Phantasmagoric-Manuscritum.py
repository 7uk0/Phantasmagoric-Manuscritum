#!/usr/bin/env python3
"""
.--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--. 
/ .. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \
\ \/\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ \/ /
 \/ /`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'\/ / 
 / /\    ____  _                 _                                             _         / /\ 
/ /\ \  |  _ \| |__   __ _ _ __ | |_ __ _ ___ _ __ ___   __ _  __ _  ___  _ __(_) ___   / /\ \
\ \/ /  | |_) | '_ \ / _` | '_ \| __/ _` / __| '_ ` _ \ / _` |/ _` |/ _ \| '__| |/ __|  \ \/ /
 \/ /   |  __/| | | | (_| | | | | || (_| \__ \ | | | | | (_| | (_| | (_) | |  | | (__    \/ / 
 / /\   |_|   |_| |_|\__,_|_| |_|\__\__,_|___/_| |_| |_|\__,_|\__, |\___/|_|  |_|\___|   / /\ 
/ /\ \                                                        |___/                     / /\ \
\ \/ /   __  __                                 _       _                               \ \/ /
 \/ /   |  \/  | __ _ _ __  _   _ ___  ___ _ __(_)_ __ | |_ _   _ _ __ ___               \/ / 
 / /\   | |\/| |/ _` | '_ \| | | / __|/ __| '__| | '_ \| __| | | | '_ ` _ \              / /\ 
/ /\ \  | |  | | (_| | | | | |_| \__ \ (__| |  | | |_) | |_| |_| | | | | | |            / /\ \
\ \/ /  |_|  |_|\__,_|_| |_|\__,_|___/\___|_|  |_| .__/ \__|\__,_|_| |_| |_|            \ \/ /
 \/ /                                            |_|                                     \/ / 
 / /\.--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--./ /\ 
/ /\ \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \/\ \
\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `' /
 `--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--' 

P H A N T A S M A G O R I C   M A N U S C R I P T U M   v1.0
Retro terminal editor with boot sequence & fax transmission
Requires: pip install pyfiglet tqdm rich

USAGE:
    python Phantasmagoric-Manuscritum.py [filename]

MODES:
    NORMAL  → default; navigate with arrow keys
    INSERT  → press [i] to type text
    COMMAND → press [:] to enter commands

COMMANDS:
    :open <file>   :save [file]   :quit   :q!   :new
    :goto <n>      :find <text>   :wq     :help
"""

import curses
import sys
import os
import time
import platform
import socket
import datetime
import random
import multiprocessing
import tkinter as tk
from tkinter import font as tkfont
import threading

# ──────────────────────────────────────────────────────────────────────────────
#  DEPENDENCY CHECK
# ──────────────────────────────────────────────────────────────────────────────
try:
    import pyfiglet
    from tqdm import tqdm
    from rich.console import Console
    from rich.progress import (Progress, SpinnerColumn, BarColumn,
                               TextColumn, TimeElapsedColumn, TaskProgressColumn)
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.columns import Columns
    from rich.rule import Rule
    from rich import print as rprint
except ImportError:
    print("\n  [!] Missing dependencies. Install them with:\n")
    print("      pip install pyfiglet tqdm rich\n")
    sys.exit(1)

console = Console()

# ══════════════════════════════════════════════════════════════════════════════
#  RETRO COLOR SCHEME (Amber/Green Phosphor)
# ══════════════════════════════════════════════════════════════════════════════
RETRO_AMBER = "#ff9900"
RETRO_GREEN = "#00ff00"
RETRO_DIM = "#886600"

# ══════════════════════════════════════════════════════════════════════════════
#  FAX PRINTER INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

# Fax constants (from original faxprint.py)
PAPER_WIDTH     = 680
WIN_WIDTH       = 800
WIN_HEIGHT      = 620
CHAR_DELAY_MS   = 18
LINE_GAP        = 2
SCAN_SPEED      = 3
FEED_SPEED      = 1.6
NOISE_CHARS     = "▓░▒█▄▀■□▪▫"
FONT_SIZE       = 13

BG_DARK        = "#0d0d0d"
MACHINE_BODY   = "#1a1a1a"
PAPER_BG       = "#e8e4d4"
PAPER_EDGE     = "#c8c4b0"
INK_COLOR      = "#1a1208"
SCAN_LINE_CLR  = "#00ff88"
SCAN_GLOW      = "#003322"
LED_ON         = "#00ff66"
LED_OFF        = "#003311"
STATUS_TEXT    = "#00cc55"
NOISE_COLOR    = "#888880"


class FaxMachine:
    def __init__(self, root, lines):
        self.root = root
        self.lines = lines
        self.current_line = 0
        self.current_char = 0
        self.paper_y = 0
        self.scan_y = 0
        self.scanning = False
        self.printing = False
        self.done = False
        self.blink_state = True
        self.led_phase = 0
        self.page_height = 0
        self.noise_cells = []
        self.char_items = []
        self.rendered_lines = []

        self._build_ui()
        self._start_sequence()

    def _build_ui(self):
        self.root.title("FAX INCOMING")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        # Detect monospace font early
        available = list(tkfont.families())
        mono_candidates = ["Courier", "Courier New", "DejaVu Sans Mono",
                           "Liberation Mono", "Monospace", "Fixed"]
        self.mono_font = "Courier"
        for c in mono_candidates:
            if c in available:
                self.mono_font = c
                break

        # TOP MACHINE CHROME
        chrome = tk.Frame(self.root, bg=MACHINE_BODY, height=70)
        chrome.pack(fill="x")
        chrome.pack_propagate(False)

        brand = tk.Label(chrome, text="FACSIMILE  MODEL  XT-9000",
                         bg=MACHINE_BODY, fg="#444444",
                         font=("Courier", 9, "bold"), anchor="w")
        brand.place(x=20, y=8)

        sub = tk.Label(chrome, text="THERMAL PRINT  •  V.34  •  33.6Kbps",
                       bg=MACHINE_BODY, fg="#2a2a2a",
                       font=("Courier", 7), anchor="w")
        sub.place(x=20, y=24)

        # LED panel
        self.led_canvas = tk.Canvas(chrome, width=180, height=40,
                                    bg=MACHINE_BODY, highlightthickness=0)
        self.led_canvas.place(x=WIN_WIDTH - 210, y=15)
        self._draw_leds()

        # Status text
        self.status_var = tk.StringVar(value="INITIALISING...")
        status_lbl = tk.Label(chrome, textvariable=self.status_var,
                              bg=MACHINE_BODY, fg=STATUS_TEXT,
                              font=("Courier", 8, "bold"))
        status_lbl.place(x=20, y=44)

        # PAPER SLOT
        slot_frame = tk.Frame(self.root, bg="#111111", height=14)
        slot_frame.pack(fill="x")
        slot_c = tk.Canvas(slot_frame, width=WIN_WIDTH, height=14,
                           bg="#111111", highlightthickness=0)
        slot_c.pack()
        for x in range(0, WIN_WIDTH, 18):
            slot_c.create_rectangle(x+3, 2, x+14, 12,
                                    fill="#222222", outline="#0a0a0a")

        # PAPER VIEWPORT
        self.viewport = tk.Canvas(
            self.root,
            width=WIN_WIDTH, height=WIN_HEIGHT - 84 - 14 - 40,
            bg=BG_DARK, highlightthickness=0, cursor="none"
        )
        self.viewport.pack(fill="x")
        self.VP_H = WIN_HEIGHT - 84 - 14 - 40

        self.PAPER_H = 4000
        self.paper_x = (WIN_WIDTH - PAPER_WIDTH) // 2

        # Paper shadow
        self.viewport.create_rectangle(
            self.paper_x + 5, 5,
            self.paper_x + PAPER_WIDTH + 5, self.PAPER_H + 5,
            fill="#000000", outline="", stipple="gray25"
        )

        # Paper body
        self.paper = self.viewport.create_rectangle(
            self.paper_x, 0,
            self.paper_x + PAPER_WIDTH, self.PAPER_H,
            fill=PAPER_BG, outline=PAPER_EDGE, width=1
        )

        self._add_paper_grain()

        # Scan bar
        self.scan_bar = self.viewport.create_rectangle(
            self.paper_x, -8,
            self.paper_x + PAPER_WIDTH, -2,
            fill=SCAN_LINE_CLR, outline="", state="hidden"
        )
        self.scan_glow = self.viewport.create_rectangle(
            self.paper_x, -20,
            self.paper_x + PAPER_WIDTH, 4,
            fill=SCAN_GLOW, outline="", state="hidden",
            stipple="gray50"
        )

        self._draw_scanlines()

        # Margin lines
        self.viewport.create_line(
            self.paper_x + 48, 0,
            self.paper_x + 48, self.PAPER_H,
            fill="#d8d4c4", width=1
        )
        self.viewport.create_line(
            self.paper_x + PAPER_WIDTH - 28, 0,
            self.paper_x + PAPER_WIDTH - 28, self.PAPER_H,
            fill="#d8d4c4", width=1
        )

        self._draw_fax_header()

        self.text_y = 110
        self.text_x = self.paper_x + 58

        # BOTTOM CHROME
        bottom = tk.Frame(self.root, bg=MACHINE_BODY, height=40)
        bottom.pack(fill="x")
        bottom.pack_propagate(False)

        self.progress_var = tk.DoubleVar(value=0)
        prog_frame = tk.Frame(bottom, bg=MACHINE_BODY)
        prog_frame.pack(side="left", padx=20, pady=10)

        tk.Label(prog_frame, text="RX", bg=MACHINE_BODY,
                 fg="#333333", font=("Courier", 7)).pack(side="left", padx=(0,5))

        self.prog_canvas = tk.Canvas(prog_frame, width=300, height=12,
                                     bg="#0a0a0a", highlightthickness=1,
                                     highlightbackground="#222222")
        self.prog_canvas.pack(side="left")
        self.prog_bar = self.prog_canvas.create_rectangle(
            0, 0, 0, 12, fill=SCAN_LINE_CLR, outline=""
        )

        tk.Label(prog_frame, text="TX", bg=MACHINE_BODY,
                 fg="#333333", font=("Courier", 7)).pack(side="left", padx=(5,0))

        self.line_count_var = tk.StringVar(value="LINE: 0000")
        tk.Label(bottom, textvariable=self.line_count_var,
                 bg=MACHINE_BODY, fg="#2a6644",
                 font=("Courier", 8, "bold")).pack(side="right", padx=20)

    def _add_paper_grain(self):
        for _ in range(900):
            x = self.paper_x + random.randint(2, PAPER_WIDTH - 2)
            y = random.randint(2, self.PAPER_H - 2)
            r = random.random()
            if r < 0.5:
                shade = random.choice(["#d0ccbc", "#c8c4b4", "#dedad0"])
                self.viewport.create_rectangle(x, y, x+1, y+1,
                                               fill=shade, outline="")
            else:
                self.viewport.create_oval(x, y, x+2, y+2,
                                          fill="#ccc8b8", outline="")

    def _draw_scanlines(self):
        for y in range(0, self.VP_H, 4):
            self.viewport.create_line(
                0, y, WIN_WIDTH, y,
                fill="#000000", width=1, stipple="gray25"
            )

    def _draw_fax_header(self):
        hfont = (self.mono_font, 7)
        bfont = (self.mono_font, 8, "bold")
        hx = self.paper_x + 8
        self.viewport.create_line(
            self.paper_x + 8, 12,
            self.paper_x + PAPER_WIDTH - 8, 12,
            fill=INK_COLOR, width=1
        )
        ts = time.strftime("%Y-%m-%d   %H:%M:%S")
        self.viewport.create_text(hx + 4, 24, anchor="w",
            text=f"DATE/TIME: {ts}",
            font=hfont, fill=INK_COLOR)
        self.viewport.create_text(hx + 4, 36, anchor="w",
            text="FROM:  +1 (408) 555-0192   XT-9000/REMOTE",
            font=hfont, fill=INK_COLOR)
        self.viewport.create_text(hx + 4, 48, anchor="w",
            text="TO:    LOCAL TERMINAL",
            font=hfont, fill=INK_COLOR)
        self.viewport.create_text(hx + 4, 60, anchor="w",
            text=f"PAGES: 001   RESOLUTION: FINE   ECM: ON",
            font=hfont, fill=INK_COLOR)

        dash = "─" * 76
        self.viewport.create_text(
            self.paper_x + PAPER_WIDTH // 2, 76,
            text=dash, font=(self.mono_font, 7), fill="#b0ac9c"
        )

        self.viewport.create_rectangle(
            self.paper_x + 8, 84,
            self.paper_x + PAPER_WIDTH - 8, 102,
            fill="#1a1208", outline=""
        )
        self.viewport.create_text(
            self.paper_x + PAPER_WIDTH // 2, 93,
            text="★  INCOMING  TRANSMISSION  ★",
            font=(self.mono_font, 8, "bold"), fill=PAPER_BG
        )

    def _draw_leds(self):
        self.led_canvas.delete("all")
        labels = ["PWR", "RX", "TX", "ERR"]
        states = [True, self.printing, False, False]
        colors = [LED_ON if s else LED_OFF for s in states]
        for i, (lbl, col) in enumerate(zip(labels, colors)):
            x = 12 + i * 44
            if col == LED_ON:
                self.led_canvas.create_oval(
                    x-8, 8, x+8, 24,
                    fill="#002211", outline=""
                )
            self.led_canvas.create_oval(
                x-5, 11, x+5, 21,
                fill=col, outline="#001a0a"
            )
            self.led_canvas.create_text(
                x, 28, text=lbl,
                font=("Courier", 6), fill="#2a2a2a"
            )

    def paper_to_view(self, y):
        return y - self.paper_y

    def _update_scan_bar_pos(self):
        vy = self.paper_to_view(self.scan_y)
        self.viewport.coords(self.scan_bar,
            self.paper_x, vy - 6,
            self.paper_x + PAPER_WIDTH, vy)
        self.viewport.coords(self.scan_glow,
            self.paper_x, vy - 18,
            self.paper_x + PAPER_WIDTH, vy + 4)

    def _start_sequence(self):
        self.status_var.set("CONNECTING...")
        self.root.after(600, self._handshake)

    def _handshake(self):
        self.status_var.set("HANDSHAKING... CNG TONE DETECTED")
        self._flash_leds(6, self._start_scan)

    def _flash_leds(self, n, callback):
        if n <= 0:
            callback()
            return
        self.printing = (n % 2 == 0)
        self._draw_leds()
        self.root.after(120, lambda: self._flash_leds(n - 1, callback))

    def _start_scan(self):
        self.status_var.set("RECEIVING FAX — PLEASE WAIT")
        self.printing = True
        self._draw_leds()
        self.scan_y = 0
        self._update_scan_bar_pos()
        self.viewport.itemconfigure(self.scan_bar, state="normal")
        self.viewport.itemconfigure(self.scan_glow, state="normal")
        self.scanning = True
        self._advance_scan()

    def _advance_scan(self):
        if not self.scanning:
            return
        self.scan_y += SCAN_SPEED
        self._update_scan_bar_pos()

        slack = self.VP_H - 60
        vy = self.paper_to_view(self.scan_y)
        if vy > slack:
            self.paper_y += FEED_SPEED
            self.viewport.move("paper_content", 0, -FEED_SPEED)

        if self.scan_y >= self.text_y:
            self.scanning = False
            self._print_next_char()
        else:
            self.root.after(8, self._advance_scan)

    def _print_next_char(self):
        if self.done:
            return

        total_lines = len(self.lines)
        if self.current_line >= total_lines:
            self._finish()
            return

        line = self.lines[self.current_line]

        if self.current_char == 0:
            self.line_item = self.viewport.create_text(
                self.text_x, self.paper_to_view(self.text_y),
                anchor="nw",
                text="",
                font=(self.mono_font, FONT_SIZE),
                fill=INK_COLOR,
                tags="paper_content"
            )
            if random.random() < 0.05:
                self._emit_noise()

        self.current_char += 1
        partial = line[:self.current_char]
        self.viewport.itemconfigure(self.line_item, text=partial)

        self.scan_y = self.text_y + 2
        self._update_scan_bar_pos()

        vy = self.paper_to_view(self.text_y)
        if vy > self.VP_H - 60:
            scroll = FEED_SPEED * 2
            self.paper_y += scroll
            self.viewport.move("paper_content", 0, -scroll)
            self.viewport.move(self.paper, 0, -scroll)

        progress = ((self.current_line + self.current_char / max(len(line), 1))
                    / total_lines)
        bar_w = int(300 * min(progress, 1.0))
        self.prog_canvas.coords(self.prog_bar, 0, 0, bar_w, 12)
        self.line_count_var.set(f"LINE: {self.current_line:04d}")

        if self.current_char >= len(line):
            self.current_char = 0
            self.current_line += 1
            self.text_y += FONT_SIZE + LINE_GAP + 4

            pause = random.randint(30, 90)
            self.root.after(pause, self._print_next_char)
        else:
            delay = CHAR_DELAY_MS + random.randint(-4, 8)
            self.root.after(max(4, delay), self._print_next_char)

    def _emit_noise(self):
        nc = random.choice(NOISE_CHARS)
        ox = self.text_x + random.randint(0, 200)
        item = self.viewport.create_text(
            ox, self.paper_to_view(self.text_y),
            anchor="nw", text=nc,
            font=(self.mono_font, FONT_SIZE),
            fill=NOISE_COLOR, tags="paper_content"
        )
        self.root.after(80, lambda: self.viewport.delete(item))

    def _finish(self):
        self.done = True
        self.viewport.itemconfigure(self.scan_bar, state="hidden")
        self.viewport.itemconfigure(self.scan_glow, state="hidden")

        dash = "─" * 76
        self.viewport.create_text(
            self.paper_x + PAPER_WIDTH // 2,
            self.paper_to_view(self.text_y + 10),
            text=dash, font=(self.mono_font, 7), fill="#b0ac9c",
            tags="paper_content"
        )
        self.viewport.create_text(
            self.paper_x + PAPER_WIDTH // 2,
            self.paper_to_view(self.text_y + 24),
            text="END OF TRANSMISSION",
            font=(self.mono_font, 8, "bold"), fill=INK_COLOR,
            tags="paper_content"
        )
        self.viewport.create_text(
            self.paper_x + PAPER_WIDTH // 2,
            self.paper_to_view(self.text_y + 36),
            text=f"TOTAL LINES: {len(self.lines):04d}   STATUS: OK   ECM: PASS",
            font=(self.mono_font, 7), fill=INK_COLOR,
            tags="paper_content"
        )

        self.prog_canvas.coords(self.prog_bar, 0, 0, 300, 12)
        self.status_var.set("TRANSMISSION COMPLETE — RECEIVED OK")
        self.printing = False
        self._draw_leds()
        self.line_count_var.set(f"LINE: {len(self.lines):04d}")
        self.root.title("FAX RECEIVED — OK")

        # Close after 3 seconds
        self.root.after(3000, self.root.destroy)


def run_fax_animation(boot_log):
    """Show fax animation in separate thread with boot log."""
    # Wrap lines to 76 chars
    WRAP = 76
    lines = []
    for raw in boot_log:
        if not raw.strip():
            lines.append("")
            continue
        while len(raw) > WRAP:
            lines.append(raw[:WRAP])
            raw = raw[WRAP:]
        lines.append(raw)

    root = tk.Tk()
    root.geometry(f"{WIN_WIDTH}x{WIN_HEIGHT}+100+80")
    
    app = FaxMachine(root, lines)
    
    root.bind("<Escape>", lambda e: root.destroy())
    root.bind("q", lambda e: root.destroy())
    root.bind("Q", lambda e: root.destroy())
    
    root.mainloop()


# ══════════════════════════════════════════════════════════════════════════════
#  BOOT SEQUENCE (Shortened but keeps all sections)
# ══════════════════════════════════════════════════════════════════════════════

LOGO_ASCII = """.--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--. 
/ .. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \\
\ \/\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ \/ /
 \/ /`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'\/ / 
 / /\    ____  _                 _                                             _         / /\\ 
/ /\ \  |  _ \| |__   __ _ _ __ | |_ __ _ ___ _ __ ___   __ _  __ _  ___  _ __(_) ___   / /\ \\
\ \/ /  | |_) | '_ \ / _` | '_ \| __/ _` / __| '_ ` _ \ / _` |/ _` |/ _ \| '__| |/ __|  \ \/ /
 \/ /   |  __/| | | | (_| | | | | || (_| \__ \ | | | | | (_| | (_| | (_) | |  | | (__    \/ / 
 / /\   |_|   |_| |_|\__,_|_| |_|\__\__,_|___/_| |_| |_|\__,_|\__, |\___/|_|  |_|\___|   / /\\ 
/ /\ \                                                        |___/                     / /\ \\
\ \/ /   __  __                                 _       _                               \ \/ /
 \/ /   |  \/  | __ _ _ __  _   _ ___  ___ _ __(_)_ __ | |_ _   _ _ __ ___               \/ / 
 / /\   | |\/| |/ _` | '_ \| | | / __|/ __| '__| | '_ \| __| | | | '_ ` _ \              / /\\ 
/ /\ \  | |  | | (_| | | | | |_| \__ \ (__| |  | | |_) | |_| |_| | | | | | |            / /\ \\
\ \/ /  |_|  |_|\__,_|_| |_|\__,_|___/\___|_|  |_| .__/ \__|\__,_|_| |_| |_|            \ \/ /
 \/ /                                            |_|                                     \/ / 
 / /\.--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--..--./ /\\ 
/ /\ \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \.. \/\ \\
\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `'\ `' /
 `--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--'`--' """


def _get_sysinfo() -> dict:
    info = {}
    info["os"]        = platform.system()
    info["release"]   = platform.release()
    info["machine"]   = platform.machine()
    info["cpu"]       = platform.processor() or "Generic x86_64"
    info["python"]    = platform.python_version()
    info["hostname"]  = socket.gethostname()
    info["datetime"]  = datetime.datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
    try:
        info["cores"] = multiprocessing.cpu_count()
    except Exception:
        info["cores"] = "N/A"
    return info


def run_boot_sequence() -> tuple:
    """Retro-styled boot sequence with fax transmission."""
    boot_start = time.time()
    sysinfo    = _get_sysinfo()
    boot_log   = []  # Collect boot messages for fax

    console.clear()

    # LOGO
    console.print(f"[{RETRO_AMBER}]{LOGO_ASCII}[/{RETRO_AMBER}]")
    console.print()

    # FIRMWARE HEADER
    console.print(
        f"[bold {RETRO_AMBER}]PhantasmaOS UEFI Firmware v2.8.4  "
        f"Copyright © 1987-2026  Manuscriptum Systems[/bold {RETRO_AMBER}]"
    )
    boot_log.append(f"PhantasmaOS UEFI Firmware v2.8.4  Copyright © 1987-2026")
    
    console.print(
        f"[{RETRO_DIM}]  CPU  : {sysinfo['cpu'][:64]}[/{RETRO_DIM}]"
    )
    boot_log.append(f"  CPU  : {sysinfo['cpu'][:64]}")
    
    console.print(
        f"[{RETRO_DIM}]  Cores: {sysinfo['cores']}   "
        f"Arch: {sysinfo['machine']}   "
        f"Host: {sysinfo['hostname']}[/{RETRO_DIM}]"
    )
    boot_log.append(f"  Cores: {sysinfo['cores']}   Arch: {sysinfo['machine']}   Host: {sysinfo['hostname']}")
    console.print()
    time.sleep(0.4)

    # MEMORY SWEEP
    console.print(f"[bold {RETRO_GREEN}]>> Memory Test ...[/bold {RETRO_GREEN}]", end="  ")
    mem_line = ">> Memory Test ...  "
    banks = [65536, 131072, 262144, 524288]
    for sz in banks:
        console.print(f"[{RETRO_DIM}]{sz:,}K[/{RETRO_DIM}]", end=" ")
        mem_line += f"{sz:,}K "
        time.sleep(0.08)
    console.print()
    boot_log.append(mem_line)
    console.print(f"[{RETRO_GREEN}]   ✔  Memory OK  (all banks passed)[/{RETRO_GREEN}]")
    boot_log.append("   ✔  Memory OK  (all banks passed)")
    time.sleep(0.3)

    # HARDWARE DETECTION
    console.print()
    console.print(Rule(f"[bold {RETRO_AMBER}]  Hardware Detection  [/bold {RETRO_AMBER}]", style=RETRO_AMBER))
    boot_log.append("─" * 76)
    boot_log.append("  HARDWARE DETECTION")
    boot_log.append("─" * 76)

    hw_items = [
        ("Detecting CPU architecture",      f"{sysinfo['machine']} / {sysinfo['os']}",  0.35),
        ("Scanning memory controllers",     "DDR4-3200  Dual-Channel  — OK",             0.35),
        ("Enumerating PCIe topology",       "Gen4 ×16  Gen3 ×4  — Ready",               0.40),
        ("Initializing GPU subsystem",      "Display adapter detected  — OK",            0.35),
        ("Mapping storage topology",        "Primary: OK   SSD: OK",                     0.40),
        ("Initializing USB controllers",    "xHCI ×2  — Ready",                         0.30),
    ]

    for label, result, delay in hw_items:
        msg = f"  {label:<48}[ {result} ]"
        console.print(
            f"  [bold {RETRO_AMBER}]{label:<48}[/bold {RETRO_AMBER}]"
            f"[{RETRO_GREEN}][ {result} ][/{RETRO_GREEN}]"
        )
        boot_log.append(msg)
        time.sleep(delay)

    time.sleep(0.3)

    # KERNEL LOG (shortened)
    console.print()
    console.print(Rule(f"[bold {RETRO_GREEN}]  Kernel Initialization  [/bold {RETRO_GREEN}]", style=RETRO_GREEN))
    boot_log.append("")
    boot_log.append("─" * 76)
    boot_log.append("  KERNEL INITIALIZATION")
    boot_log.append("─" * 76)

    kernel_log = [
        ("[    0.000000] Linux PhantasmaOS kernel 6.8.0-retro #1 SMP",         RETRO_AMBER,    0.05),
        ("[    0.005000] clocksource: tsc-early registered",                   RETRO_DIM,      0.05),
        ("[    0.012000] Linux version 6.8.0 (gcc version 13.2.0)",            RETRO_AMBER,    0.06),
        ("[    0.020000] Mounting root filesystem (read-only)",                RETRO_GREEN,    0.07),
        ("[    0.027000] EXT4-fs (nvme0n1p2): recovery complete",              RETRO_GREEN,    0.07),
        (f"[    0.050000] systemd[1]: Hostname set to <{sysinfo['hostname']}>.", RETRO_AMBER, 0.08),
    ]

    for msg, color, delay in kernel_log:
        console.print(f"[{color}]{msg}[/{color}]")
        boot_log.append(msg)
        time.sleep(delay)

    # SERVICES (shortened)
    console.print()
    console.print(Rule(f"[bold {RETRO_AMBER}]  Starting Services  [/bold {RETRO_AMBER}]", style=RETRO_AMBER))
    boot_log.append("")
    boot_log.append("─" * 76)
    boot_log.append("  STARTING SERVICES")
    boot_log.append("─" * 76)

    with Progress(
        SpinnerColumn(style=RETRO_GREEN),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style=RETRO_GREEN, finished_style=RETRO_AMBER),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        services = [
            ("Mounting filesystems", 25),
            ("Starting network", 30),
            ("Loading text subsystem", 28),
            ("Initializing editor core", 32),
        ]
        for desc, steps in services:
            task = progress.add_task(f"[{RETRO_DIM}]{desc}...", total=steps)
            boot_log.append(f"  {desc}...")
            for _ in range(steps):
                progress.update(task, advance=1)
                time.sleep(0.02)
            boot_log.append(f"  {desc}... DONE")

    time.sleep(0.4)

    # BOOT COMPLETE
    console.print()
    console.print(f"[bold {RETRO_GREEN}]✓  BOOT COMPLETE  —  System ready[/bold {RETRO_GREEN}]")
    boot_log.append("")
    boot_log.append("✓  BOOT COMPLETE  —  System ready")
    elapsed = time.time() - boot_start
    console.print(f"[{RETRO_DIM}]   Boot time: {elapsed:.2f}s[/{RETRO_DIM}]")
    boot_log.append(f"   Boot time: {elapsed:.2f}s")
    console.print()
    time.sleep(0.5)

    # PREPARE TO LAUNCH FAX
    console.print(f"[bold {RETRO_AMBER}]→  Receiving system initialization fax...[/bold {RETRO_AMBER}]")
    console.print()
    time.sleep(1.0)

    # Show fax animation
    run_fax_animation(boot_log)

    console.clear()
    console.print(f"[bold {RETRO_GREEN}]✓  FAX RECEIVED  —  Launching editor...[/bold {RETRO_GREEN}]\n")
    time.sleep(1.0)

    return sysinfo, boot_start


# ══════════════════════════════════════════════════════════════════════════════
#  TEXT BUFFER
# ══════════════════════════════════════════════════════════════════════════════

class TextBuffer:
    def __init__(self, filepath: str = None):
        self.filepath    = filepath
        self.lines       = [""]
        self.cursor_row  = 0
        self.cursor_col  = 0
        self.modified    = False

        if filepath and os.path.isfile(filepath):
            self.load(filepath)

    def load(self, filepath: str) -> tuple:
        """Returns (success, message)."""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                self.lines = f.read().splitlines()
            if not self.lines:
                self.lines = [""]
            self.filepath    = filepath
            self.cursor_row  = 0
            self.cursor_col  = 0
            self.modified    = False
            return True, f"Loaded '{filepath}' ({len(self.lines)} lines)"
        except Exception as e:
            return False, f"Error loading file: {e}"

    def save(self, filepath: str = None) -> tuple:
        """Returns (success, message)."""
        target = filepath or self.filepath
        if not target:
            return False, "No filename specified. Use :save <filename>"
        try:
            with open(target, "w", encoding="utf-8") as f:
                f.write("\n".join(self.lines))
            self.filepath = target
            self.modified = False
            return True, f"Saved to '{target}' ({len(self.lines)} lines)"
        except Exception as e:
            return False, f"Error saving file: {e}"

    def insert_char(self, char: str):
        row = self.lines[self.cursor_row]
        self.lines[self.cursor_row] = row[:self.cursor_col] + char + row[self.cursor_col:]
        self.cursor_col += 1
        self.modified = True

    def backspace(self):
        if self.cursor_col > 0:
            row = self.lines[self.cursor_row]
            self.lines[self.cursor_row] = row[:self.cursor_col - 1] + row[self.cursor_col:]
            self.cursor_col -= 1
            self.modified = True
        elif self.cursor_row > 0:
            prev = self.lines[self.cursor_row - 1]
            curr = self.lines[self.cursor_row]
            self.lines[self.cursor_row - 1] = prev + curr
            del self.lines[self.cursor_row]
            self.cursor_row -= 1
            self.cursor_col = len(prev)
            self.modified = True

    def newline(self):
        row = self.lines[self.cursor_row]
        left = row[:self.cursor_col]
        right = row[self.cursor_col:]
        self.lines[self.cursor_row] = left
        self.lines.insert(self.cursor_row + 1, right)
        self.cursor_row += 1
        self.cursor_col = 0
        self.modified = True

    def move(self, drow: int = 0, dcol: int = 0):
        self.cursor_row = max(0, min(len(self.lines) - 1, self.cursor_row + drow))
        self.cursor_col = max(0, min(len(self.lines[self.cursor_row]), self.cursor_col + dcol))

    def find(self, needle: str) -> tuple:
        """Returns (row, col) or None."""
        for r, line in enumerate(self.lines):
            idx = line.find(needle)
            if idx != -1:
                return (r, idx)
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  CURSES EDITOR
# ══════════════════════════════════════════════════════════════════════════════

MODE_NORMAL  = 0
MODE_INSERT  = 1
MODE_COMMAND = 2

# Retro color pairs
COLOR_RETRO_TEXT  = 1    # Amber text on black
COLOR_RETRO_UI    = 2    # Green UI on black
COLOR_RETRO_ERROR = 3    # Bright red on black
COLOR_RETRO_DIM   = 4    # Dim amber


class PhantasmagoricEditor:
    def __init__(self, scr, sysinfo, boot_start, initial_file=None):
        self.scr         = scr
        self.sysinfo     = sysinfo
        self.boot_start  = boot_start
        self.running     = True
        self.mode        = MODE_NORMAL
        self.cmd_buf     = ""
        self.message     = ""
        self.msg_type    = "info"

        self.buf = TextBuffer(initial_file)

        curses.curs_set(1)
        curses.use_default_colors()
        
        # Initialize retro color pairs
        curses.init_pair(COLOR_RETRO_TEXT, 214, -1)    # Amber
        curses.init_pair(COLOR_RETRO_UI, 46, -1)       # Bright green
        curses.init_pair(COLOR_RETRO_ERROR, 196, -1)   # Bright red
        curses.init_pair(COLOR_RETRO_DIM, 136, -1)     # Dim amber

        self.scr.timeout(1000)
        self._compute_layout()

    def _compute_layout(self):
        h, w = self.scr.getmaxyx()
        self.term_h = h
        self.term_w = w
        self.logo_h = 4
        self.status_h = 2
        self.editor_h = max(1, h - self.logo_h - self.status_h - 1)

    def render(self):
        self.scr.erase()
        h, w = self.term_h, self.term_w

        # LOGO (4 lines)
        logo_lines = [
            "╔═══════════════════════════════════════════════════════════════════════════╗",
            "║  PHANTASMAGORIC MANUSCRIPTUM v1.0  —  Retro Text Editor with Style      ║",
            "║  System Uptime: {uptime}                                                  ║",
            "╚═══════════════════════════════════════════════════════════════════════════╝",
        ]
        
        uptime = int(time.time() - self.boot_start)
        logo_lines[2] = logo_lines[2].format(uptime=f"{uptime}s")
        
        for i, line in enumerate(logo_lines[:self.logo_h]):
            padded = line.ljust(w)[:w]
            self.scr.addstr(i, 0, padded, curses.color_pair(COLOR_RETRO_UI) | curses.A_BOLD)

        # TEXT AREA
        start_row = self.buf.cursor_row - self.editor_h // 2
        start_row = max(0, min(len(self.buf.lines) - self.editor_h, start_row))

        for i in range(self.editor_h):
            line_num = start_row + i
            y = self.logo_h + i

            if line_num < len(self.buf.lines):
                # Line number
                lnum_str = f"{line_num + 1:4d} │ "
                self.scr.addstr(y, 0, lnum_str, curses.color_pair(COLOR_RETRO_DIM))

                # Text
                text = self.buf.lines[line_num]
                visible = text[:w - len(lnum_str)]
                self.scr.addstr(y, len(lnum_str), visible, curses.color_pair(COLOR_RETRO_TEXT))
            else:
                self.scr.addstr(y, 0, "   ~ ", curses.color_pair(COLOR_RETRO_DIM))

        # STATUS BAR
        status_y = self.logo_h + self.editor_h
        mode_str = {
            MODE_NORMAL:  "[NORMAL]",
            MODE_INSERT:  "[INSERT]",
            MODE_COMMAND: "[COMMAND]",
        }[self.mode]

        fname = os.path.basename(self.buf.filepath) if self.buf.filepath else "[No Name]"
        mod = " [+]" if self.buf.modified else ""
        pos = f"L{self.buf.cursor_row + 1}:C{self.buf.cursor_col + 1}"

        left = f" {mode_str}  {fname}{mod}"
        right = f"{pos}  {len(self.buf.lines)} lines "
        spaces = w - len(left) - len(right)
        status_line = left + (" " * max(0, spaces)) + right

        self.scr.addstr(status_y, 0, status_line[:w], 
                       curses.color_pair(COLOR_RETRO_UI) | curses.A_REVERSE)

        # MESSAGE/COMMAND LINE
        msg_y = status_y + 1
        if self.mode == MODE_COMMAND:
            display = f":{self.cmd_buf}"
            self.scr.addstr(msg_y, 0, display[:w], curses.color_pair(COLOR_RETRO_TEXT))
        elif self.message:
            color = COLOR_RETRO_ERROR if self.msg_type == "error" else COLOR_RETRO_UI
            self.scr.addstr(msg_y, 0, self.message[:w], curses.color_pair(color))

        # CURSOR
        view_row = self.buf.cursor_row - start_row
        if 0 <= view_row < self.editor_h:
            cursor_y = self.logo_h + view_row
            cursor_x = 7 + self.buf.cursor_col
            cursor_x = min(cursor_x, w - 1)
            try:
                self.scr.move(cursor_y, cursor_x)
            except:
                pass

        self.scr.refresh()

    def run_command(self, cmd: str):
        parts = cmd.strip().split(maxsplit=1)
        if not parts:
            return
        verb = parts[0].lower()
        arg  = parts[1] if len(parts) > 1 else ""

        if verb in ("q", "quit"):
            if self.buf.modified:
                self.message  = "Unsaved changes!  Use  :q!  to discard  or  :w  to save first."
                self.msg_type = "error"
            else:
                self.running = False

        elif verb in ("q!", "quit!"):
            self.running = False

        elif verb in ("w", "save"):
            ok, msg = self.buf.save(arg or None)
            self.message  = msg
            self.msg_type = "success" if ok else "error"

        elif verb in ("wq", "x"):
            ok, msg = self.buf.save(arg or None)
            if ok:
                self.running = False
            else:
                self.message  = msg
                self.msg_type = "error"

        elif verb in ("o", "open", "e", "edit"):
            if not arg:
                self.message  = "Usage:  :open <filename>"
                self.msg_type = "error"
            else:
                ok, msg = self.buf.load(arg)
                self.message  = msg
                self.msg_type = "success" if ok else "error"

        elif verb in ("n", "new"):
            self.buf      = TextBuffer()
            self.message  = "New empty buffer created."
            self.msg_type = "success"

        elif verb in ("g", "goto", "go"):
            try:
                n = max(0, min(len(self.buf.lines) - 1, int(arg) - 1))
                self.buf.cursor_row = n
                self.buf.cursor_col = 0
                self.message  = f"Jumped to line {n + 1}."
                self.msg_type = "info"
            except ValueError:
                self.message  = "Usage:  :goto <line number>"
                self.msg_type = "error"

        elif verb in ("f", "find", "/"):
            if not arg:
                self.message  = "Usage:  :find <text>"
                self.msg_type = "error"
            else:
                result = self.buf.find(arg)
                if result:
                    self.buf.cursor_row, self.buf.cursor_col = result
                    self.message  = f"Found '{arg}' at line {result[0] + 1}, col {result[1] + 1}."
                    self.msg_type = "success"
                else:
                    self.message  = f"'{arg}' not found in buffer."
                    self.msg_type = "error"

        elif verb in ("h", "help", "?"):
            self.message = (
                ":open <f>  :save [f]  :quit  :q!  :wq  :new  "
                ":goto <n>  :find <t>  |  i=INSERT  ESC=NORMAL  :=COMMAND"
            )
            self.msg_type = "info"

        else:
            self.message  = f"Unknown command '{verb}'.  Try  :help"
            self.msg_type = "error"

    def handle_normal(self, key: int):
        if key == ord("i"):
            self.mode    = MODE_INSERT
            self.message = "-- INSERT mode --  ESC to return to NORMAL"
            self.msg_type = "info"
        elif key == ord(":"):
            self.mode    = MODE_COMMAND
            self.cmd_buf = ""
            self.message = ""
        elif key in (ord("q"), ord("Q")):
            if self.buf.modified:
                self.message  = "Unsaved changes!  :q! to force quit  :w to save."
                self.msg_type = "error"
            else:
                self.running = False
        elif key == curses.KEY_UP:
            self.buf.move(-1)
        elif key == curses.KEY_DOWN:
            self.buf.move(1)
        elif key == curses.KEY_LEFT:
            self.buf.move(dcol=-1)
        elif key == curses.KEY_RIGHT:
            self.buf.move(dcol=1)
        elif key == curses.KEY_PPAGE:
            self.buf.move(-self.editor_h)
        elif key == curses.KEY_NPAGE:
            self.buf.move(self.editor_h)
        elif key == curses.KEY_HOME:
            self.buf.cursor_col = 0
        elif key == curses.KEY_END:
            self.buf.cursor_col = len(self.buf.lines[self.buf.cursor_row])

    def handle_insert(self, key: int):
        if key == 27:
            self.mode     = MODE_NORMAL
            self.message  = ""
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            self.buf.backspace()
        elif key in (curses.KEY_ENTER, 10, 13):
            self.buf.newline()
        elif key == curses.KEY_UP:
            self.buf.move(-1)
        elif key == curses.KEY_DOWN:
            self.buf.move(1)
        elif key == curses.KEY_LEFT:
            self.buf.move(dcol=-1)
        elif key == curses.KEY_RIGHT:
            self.buf.move(dcol=1)
        elif key == curses.KEY_HOME:
            self.buf.cursor_col = 0
        elif key == curses.KEY_END:
            self.buf.cursor_col = len(self.buf.lines[self.buf.cursor_row])
        elif 32 <= key <= 126:
            self.buf.insert_char(chr(key))

    def handle_command(self, key: int):
        if key == 27:
            self.mode     = MODE_NORMAL
            self.cmd_buf  = ""
            self.message  = "Command cancelled."
            self.msg_type = "info"
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            if self.cmd_buf:
                self.cmd_buf = self.cmd_buf[:-1]
            else:
                self.mode    = MODE_NORMAL
                self.message = ""
        elif key in (curses.KEY_ENTER, 10, 13):
            self.run_command(self.cmd_buf)
            self.cmd_buf = ""
            if self.running:
                self.mode = MODE_NORMAL
        elif 32 <= key <= 126:
            self.cmd_buf += chr(key)

    def run(self):
        while self.running:
            self.render()
            key = self.scr.getch()
            if key == -1:
                continue

            if self.mode == MODE_NORMAL:
                self.handle_normal(key)
            elif self.mode == MODE_INSERT:
                self.handle_insert(key)
            elif self.mode == MODE_COMMAND:
                self.handle_command(key)


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

def main():
    initial_file = sys.argv[1] if len(sys.argv) > 1 else None

    # 1. Boot sequence with fax
    sysinfo, boot_start = run_boot_sequence()

    # 2. Launch curses editor
    def _run(stdscr):
        editor = PhantasmagoricEditor(stdscr, sysinfo, boot_start, initial_file)
        editor.run()

    curses.wrapper(_run)

    # 3. Goodbye
    console.print(f"\n[bold {RETRO_AMBER}]  Phantasmagoric Manuscriptum closed. Session ended. Goodbye![/bold {RETRO_AMBER}]\n")


if __name__ == "__main__":
    main()
