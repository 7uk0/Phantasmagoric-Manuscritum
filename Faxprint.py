#!/usr/bin/env python3
"""
faxprint.py — Retro Fax Machine Animator
Usage: python3 faxprint.py yourfile.txt
"""

import tkinter as tk
from tkinter import font as tkfont
import sys
import os
import time
import random
import math

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
PAPER_WIDTH     = 680          # px width of the paper strip
WIN_WIDTH       = 800
WIN_HEIGHT      = 620
CHAR_DELAY_MS   = 18           # ms per character typed
LINE_GAP        = 2            # extra px between lines
SCAN_SPEED      = 3            # px per frame for scan bar
FEED_SPEED      = 1.6          # px per frame paper scroll
NOISE_CHARS     = "▓░▒█▄▀■□▪▫" # glitch noise chars
FONT_SIZE       = 13

# Colour palette ─ thermal paper / phosphor green
BG_DARK        = "#0d0d0d"
MACHINE_BODY   = "#1a1a1a"
PAPER_BG       = "#e8e4d4"     # aged thermal paper
PAPER_EDGE     = "#c8c4b0"
INK_COLOR      = "#1a1208"     # faint thermal ink
SCAN_LINE_CLR  = "#00ff88"     # phosphor green scan bar
SCAN_GLOW      = "#003322"
LED_ON         = "#00ff66"
LED_OFF        = "#003311"
STATUS_TEXT    = "#00cc55"
NOISE_COLOR    = "#888880"


# ─────────────────────────────────────────────
class FaxMachine:
    def __init__(self, root, lines):
        self.root = root
        self.lines = lines
        self.current_line = 0
        self.current_char = 0
        self.paper_y = 0          # how far paper has scrolled up
        self.scan_y = 0
        self.scanning = False
        self.printing = False
        self.done = False
        self.blink_state = True
        self.led_phase = 0
        self.page_height = 0      # total rendered text height so far
        self.noise_cells = []
        self.char_items = []      # canvas text items for typed chars
        self.rendered_lines = []  # (y_pos, text) already drawn

        self._build_ui()
        self._start_sequence()

    # ── UI CONSTRUCTION ──────────────────────
    def _build_ui(self):
        self.root.title("FAX INCOMING")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        # Detect monospace font early — needed by _draw_fax_header
        available = list(tkfont.families())
        mono_candidates = ["Courier", "Courier New", "DejaVu Sans Mono",
                           "Liberation Mono", "Monospace", "Fixed"]
        self.mono_font = "Courier"
        for c in mono_candidates:
            if c in available:
                self.mono_font = c
                break

        # ── TOP MACHINE CHROME ───────────────
        chrome = tk.Frame(self.root, bg=MACHINE_BODY, height=70)
        chrome.pack(fill="x")
        chrome.pack_propagate(False)

        # Brand label
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

        # ── PAPER SLOT ───────────────────────
        slot_frame = tk.Frame(self.root, bg="#111111", height=14)
        slot_frame.pack(fill="x")
        # slot teeth
        slot_c = tk.Canvas(slot_frame, width=WIN_WIDTH, height=14,
                           bg="#111111", highlightthickness=0)
        slot_c.pack()
        for x in range(0, WIN_WIDTH, 18):
            slot_c.create_rectangle(x+3, 2, x+14, 12,
                                    fill="#222222", outline="#0a0a0a")

        # ── PAPER VIEWPORT ───────────────────
        self.viewport = tk.Canvas(
            self.root,
            width=WIN_WIDTH, height=WIN_HEIGHT - 84 - 14 - 40,
            bg=BG_DARK, highlightthickness=0, cursor="none"
        )
        self.viewport.pack(fill="x")
        self.VP_H = WIN_HEIGHT - 84 - 14 - 40

        # Paper strip (taller than viewport; we scroll it)
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

        # Paper grain texture (random dots)
        self._add_paper_grain()

        # Scan bar (green glow)
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

        # CRT scanline overlay
        self._draw_scanlines()

        # Margin lines on paper (like real fax)
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

        # Page header on paper
        self._draw_fax_header()

        # Text start offset (below header)
        self.text_y = 110      # absolute y in paper coords
        self.text_x = self.paper_x + 58

        # ── BOTTOM CHROME ────────────────────
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

        # Line counter
        self.line_count_var = tk.StringVar(value="LINE: 0000")
        tk.Label(bottom, textvariable=self.line_count_var,
                 bg=MACHINE_BODY, fg="#2a6644",
                 font=("Courier", 8, "bold")).pack(side="right", padx=20)


    # ── PAPER TEXTURES ────────────────────────
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
        """Overlay horizontal CRT lines across whole viewport."""
        for y in range(0, self.VP_H, 4):
            self.viewport.create_line(
                0, y, WIN_WIDTH, y,
                fill="#000000", width=1, stipple="gray25"
            )

    def _draw_fax_header(self):
        """Print the fax transmission header onto the paper."""
        hfont = (self.mono_font, 7)
        bfont = (self.mono_font, 8, "bold")
        hx = self.paper_x + 12
        # Top divider
        self.viewport.create_line(
            self.paper_x + 12, 12,
            self.paper_x + PAPER_WIDTH - 12, 12,
            fill=INK_COLOR, width=1
        )
        ts = time.strftime("%Y-%m-%d %H:%M")
        self.viewport.create_text(hx, 24, anchor="w",
            text=f"DATE/TIME: {ts}",
            font=hfont, fill=INK_COLOR)
        self.viewport.create_text(hx, 36, anchor="w",
            text="FROM: +1(408)555-0192  XT-9000",
            font=hfont, fill=INK_COLOR)
        self.viewport.create_text(hx, 48, anchor="w",
            text="TO: LOCAL TERMINAL",
            font=hfont, fill=INK_COLOR)
        self.viewport.create_text(hx, 60, anchor="w",
            text=f"PAGES: 001  RES: FINE  ECM: ON",
            font=hfont, fill=INK_COLOR)

        # Dashed separator
        dash = "─" * 76
        self.viewport.create_text(
            self.paper_x + PAPER_WIDTH // 2, 76,
            text=dash, font=(self.mono_font, 7), fill="#b0ac9c"
        )

        # Big title bar
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
        """Draw LED status indicators."""
        self.led_canvas.delete("all")
        labels = ["PWR", "RX", "TX", "ERR"]
        states = [True,
                  self.printing,
                  False,
                  False]
        colors = [LED_ON if s else LED_OFF for s in states]
        for i, (lbl, col) in enumerate(zip(labels, colors)):
            x = 12 + i * 44
            # LED glow
            if col == LED_ON:
                self.led_canvas.create_oval(
                    x-8, 8, x+8, 24,
                    fill="#002211", outline=""
                )
            # LED bulb
            self.led_canvas.create_oval(
                x-5, 11, x+5, 21,
                fill=col, outline="#001a0a"
            )
            self.led_canvas.create_text(
                x, 28, text=lbl,
                font=("Courier", 6), fill="#2a2a2a"
            )

    # ── COORDINATE HELPERS ───────────────────
    def paper_to_view(self, y):
        """Convert paper absolute-y to current viewport y."""
        return y - self.paper_y

    def _scroll_paper(self, dy):
        """Move all paper items up by dy pixels."""
        self.viewport.move("paper_content", 0, -dy)
        # also move paper rect + grain etc.
        self.viewport.move(self.paper, 0, -dy)
        self.viewport.move(self.scan_bar, 0, -dy)
        self.viewport.move(self.scan_glow, 0, -dy)

    # ── MAIN SEQUENCE ────────────────────────
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
        # Show scan bar at top of paper (in viewport coords)
        self.scan_y = 0
        self._update_scan_bar_pos()
        self.viewport.itemconfigure(self.scan_bar, state="normal")
        self.viewport.itemconfigure(self.scan_glow, state="normal")
        self.scanning = True
        self._advance_scan()

    def _update_scan_bar_pos(self):
        vy = self.paper_to_view(self.scan_y)
        self.viewport.coords(self.scan_bar,
            self.paper_x, vy - 6,
            self.paper_x + PAPER_WIDTH, vy)
        self.viewport.coords(self.scan_glow,
            self.paper_x, vy - 18,
            self.paper_x + PAPER_WIDTH, vy + 4)

    def _advance_scan(self):
        """Scan bar moves down; when it hits text_y, start printing."""
        if not self.scanning:
            return
        self.scan_y += SCAN_SPEED
        self._update_scan_bar_pos()

        # Scroll paper if scan bar near bottom of viewport
        slack = self.VP_H - 60
        vy = self.paper_to_view(self.scan_y)
        if vy > slack:
            self.paper_y += FEED_SPEED
            self.viewport.move("paper_content", 0, -FEED_SPEED)

        if self.scan_y >= self.text_y:
            # begin character printing
            self.scanning = False
            self._print_next_char()
        else:
            self.root.after(8, self._advance_scan)

    # ── TEXT PRINTING ────────────────────────
    def _print_next_char(self):
        if self.done:
            return

        total_lines = len(self.lines)
        if self.current_line >= total_lines:
            self._finish()
            return

        line = self.lines[self.current_line]

        if self.current_char == 0:
            # Reserve vertical space for this line
            self.line_item = self.viewport.create_text(
                self.text_x, self.paper_to_view(self.text_y),
                anchor="nw",
                text="",
                font=(self.mono_font, FONT_SIZE),
                fill=INK_COLOR,
                tags="paper_content"
            )
            # Occasionally add noise char then erase
            if random.random() < 0.05:
                self._emit_noise()

        # Append one character
        self.current_char += 1
        partial = line[:self.current_char]
        self.viewport.itemconfigure(self.line_item, text=partial)

        # Advance scan bar with text
        self.scan_y = self.text_y + 2
        self._update_scan_bar_pos()

        # Scroll if needed
        vy = self.paper_to_view(self.text_y)
        if vy > self.VP_H - 60:
            scroll = FEED_SPEED * 2
            self.paper_y += scroll
            self.viewport.move("paper_content", 0, -scroll)
            self.viewport.move(self.paper, 0, -scroll)

        # Update progress
        progress = ((self.current_line + self.current_char / max(len(line), 1))
                    / total_lines)
        bar_w = int(300 * min(progress, 1.0))
        self.prog_canvas.coords(self.prog_bar, 0, 0, bar_w, 12)
        self.line_count_var.set(f"LINE: {self.current_line:04d}")

        if self.current_char >= len(line):
            # Line done — move to next
            self.current_char = 0
            self.current_line += 1
            self.text_y += FONT_SIZE + LINE_GAP + 4

            # Schedule next line with a brief pause
            pause = random.randint(30, 90)
            self.root.after(pause, self._print_next_char)
        else:
            # Slightly variable typing speed for realism
            delay = CHAR_DELAY_MS + random.randint(-4, 8)
            self.root.after(max(4, delay), self._print_next_char)

    def _emit_noise(self):
        """Flash a random noise char briefly."""
        nc = random.choice(NOISE_CHARS)
        ox = self.text_x + random.randint(0, 200)
        item = self.viewport.create_text(
            ox, self.paper_to_view(self.text_y),
            anchor="nw", text=nc,
            font=(self.mono_font, FONT_SIZE),
            fill=NOISE_COLOR, tags="paper_content"
        )
        self.root.after(80, lambda: self.viewport.delete(item))

    # ── FINISH ───────────────────────────────
    def _finish(self):
        self.done = True
        self.viewport.itemconfigure(self.scan_bar, state="hidden")
        self.viewport.itemconfigure(self.scan_glow, state="hidden")

        # Print footer
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

        # Blink status
        self._blink_done()

    def _blink_done(self):
        if self.blink_state:
            self.status_var.set("TRANSMISSION COMPLETE — RECEIVED OK")
        else:
            self.status_var.set("")
        self.blink_state = not self.blink_state
        self.root.after(600, self._blink_done)


# ─────────────────────────────────────────────
def main():
    if len(sys.argv) < 2:
        print("Usage: python3 faxprint.py <textfile.txt>")
        sys.exit(1)

    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"Error: file not found — {path}")
        sys.exit(1)

    with open(path, "r", errors="replace") as f:
        raw_lines = f.read().splitlines()

    # Wrap long lines to fit paper width (adjusted for margins)
    WRAP = 76
    lines = []
    for raw in raw_lines:
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

    # ESC or Q to quit
    root.bind("<Escape>", lambda e: root.destroy())
    root.bind("q", lambda e: root.destroy())
    root.bind("Q", lambda e: root.destroy())

    root.mainloop()


if __name__ == "__main__":
    main()