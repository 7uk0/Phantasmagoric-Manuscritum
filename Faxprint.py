#!/usr/bin/env python3
"""
faxprint.py — Retro Fax Machine Animator (Soundless Edition)
Usage: python3 faxprint.py yourfile.txt
"""

import tkinter as tk
from tkinter import font as tkfont
import sys, os, time, random, math

# ─────────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────────
PAPER_WIDTH   = 680
WIN_WIDTH     = 800
WIN_HEIGHT    = 660
CHROME_H      = 130
CHAR_DELAY_MS = 18
LINE_GAP      = 2
SCAN_SPEED    = 3
FEED_SPEED    = 1.6
NOISE_CHARS   = "▓░▒█▄▀■□▪▫"
FONT_SIZE     = 13

# Machine colour palette
BG_DARK       = "#0d0d0d"
MACHINE_BODY  = "#1a1a1a"
PAPER_BG      = "#e8e4d4"
PAPER_EDGE    = "#c8c4b0"
INK_COLOR     = "#1a1208"
SCAN_LINE_CLR = "#00ff88"
SCAN_GLOW     = "#003322"
LED_ON        = "#00ff66"
LED_OFF       = "#003311"
STATUS_TEXT   = "#00cc55"
NOISE_COLOR   = "#888880"

# Amber CRT palette
CRT_BG        = "#0b0700"
CRT_AMBER     = "#ffb300"
CRT_DIM       = "#996a00"
CRT_GLOW      = "#331500"


# ─────────────────────────────────────────────
class FaxMachine:
    def __init__(self, root, lines):
        self.root         = root
        self.lines        = lines
        self.current_line = 0
        self.current_char = 0
        self.paper_y      = 0
        self.scan_y       = 0
        self.scanning     = False
        self.printing     = False
        self.done         = False
        self.blink_state  = True

        self._build_ui()
        self._start_sequence()

    # ─────────────────────────────────────────
    #  UI CONSTRUCTION
    # ─────────────────────────────────────────
    def _build_ui(self):
        self.root.title("FAX INCOMING")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(False, False)

        # Pick best available monospace font
        available = set(tkfont.families())
        for cand in ["Courier New", "Courier", "DejaVu Sans Mono",
                     "Liberation Mono", "Monospace", "Fixed"]:
            if cand in available:
                self.mono_font = cand
                break
        else:
            self.mono_font = "Courier"

        # ── TOP CHROME ──────────────────────
        chrome = tk.Frame(self.root, bg=MACHINE_BODY, height=CHROME_H)
        chrome.pack(fill="x")
        chrome.pack_propagate(False)

        # Brand / sub-title (left side)
        tk.Label(chrome, text="FAXSIMILE  MODEL  XT-9000",
                 bg=MACHINE_BODY, fg="#444444",
                 font=("Courier", 9, "bold"), anchor="w").place(x=20, y=8)
        tk.Label(chrome, text="THERMAL PRINT  •  V.34",
                 bg=MACHINE_BODY, fg="#2a2a2a",
                 font=("Courier", 7), anchor="w").place(x=20, y=24)

        # Status readout (left side, below brand)
        self.status_var = tk.StringVar(value="INITIALISING...")
        tk.Label(chrome, textvariable=self.status_var,
                 bg=MACHINE_BODY, fg=STATUS_TEXT,
                 font=("Courier", 8, "bold")).place(x=20, y=44)

        # LED indicators (right side)
        self.led_canvas = tk.Canvas(chrome, width=180, height=50,
                                    bg=MACHINE_BODY, highlightthickness=0)
        self.led_canvas.place(x=WIN_WIDTH - 208, y=8)
        self._draw_leds()

        # ── AMBER CRT DISPLAY (centred) ──────
        self._build_crt_display(chrome)

        # ── PAPER SLOT TEETH ────────────────
        slot = tk.Canvas(self.root, width=WIN_WIDTH, height=14,
                         bg="#111111", highlightthickness=0)
        slot.pack(fill="x")
        for x in range(0, WIN_WIDTH, 18):
            slot.create_rectangle(x + 3, 2, x + 14, 12,
                                  fill="#222222", outline="#0a0a0a")

        # ── PAPER VIEWPORT ──────────────────
        self.VP_H = WIN_HEIGHT - CHROME_H - 14 - 40
        self.viewport = tk.Canvas(
            self.root, width=WIN_WIDTH, height=self.VP_H,
            bg=BG_DARK, highlightthickness=0, cursor="none"
        )
        self.viewport.pack(fill="x")

        self.PAPER_H = 4000
        self.paper_x = (WIN_WIDTH - PAPER_WIDTH) // 2

        # Paper shadow
        self.paper_shadow = self.viewport.create_rectangle(
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

        # Paper grain texture
        self._add_paper_grain()

        # Scan bar
        self.scan_bar = self.viewport.create_rectangle(
            self.paper_x, -8, self.paper_x + PAPER_WIDTH, -2,
            fill=SCAN_LINE_CLR, outline="", state="hidden"
        )
        self.scan_glow = self.viewport.create_rectangle(
            self.paper_x, -20, self.paper_x + PAPER_WIDTH, 4,
            fill=SCAN_GLOW, outline="", state="hidden", stipple="gray50"
        )

        # CRT scanline overlay
        self._draw_scanlines()

        # Margin rules
        for rx in (self.paper_x + 48, self.paper_x + PAPER_WIDTH - 28):
            self.viewport.create_line(
                rx, 0, rx, self.PAPER_H,
                fill="#d8d4c4", width=1, tags="paper_content"
            )

        # Paper title
        self._draw_paper_title()

        self.text_y = 38
        self.text_x = self.paper_x + 58

        # ── BOTTOM CHROME ───────────────────
        bottom = tk.Frame(self.root, bg=MACHINE_BODY, height=40)
        bottom.pack(fill="x")
        bottom.pack_propagate(False)

        pf = tk.Frame(bottom, bg=MACHINE_BODY)
        pf.pack(side="left", padx=20, pady=10)
        tk.Label(pf, text="RX", bg=MACHINE_BODY,
                 fg="#333333", font=("Courier", 7)).pack(side="left", padx=(0, 5))
        self.prog_canvas = tk.Canvas(pf, width=300, height=12,
                                     bg="#0a0a0a", highlightthickness=1,
                                     highlightbackground="#222222")
        self.prog_canvas.pack(side="left")
        self.prog_bar = self.prog_canvas.create_rectangle(
            0, 0, 0, 12, fill=SCAN_LINE_CLR, outline=""
        )
        tk.Label(pf, text="TX", bg=MACHINE_BODY,
                 fg="#333333", font=("Courier", 7)).pack(side="left", padx=(5, 0))

        self.line_count_var = tk.StringVar(value="LINE: 0000")
        tk.Label(bottom, textvariable=self.line_count_var,
                 bg=MACHINE_BODY, fg="#2a6644",
                 font=("Courier", 8, "bold")).pack(side="right", padx=20)

    # ─────────────────────────────────────────
    def _build_crt_display(self, chrome):
        CRT_W, CRT_H = 370, 82
        CRT_X = (WIN_WIDTH - CRT_W) // 2
        CRT_Y = 24

        # Outer bezel
        bezel = tk.Frame(chrome,
                         bg="#141414",
                         highlightbackground="#3a3a3a",
                         highlightthickness=2,
                         relief="sunken", bd=3)
        bezel.place(x=CRT_X - 7, y=CRT_Y - 6,
                    width=CRT_W + 14, height=CRT_H + 12)

        # Screen canvas
        self.crt = tk.Canvas(bezel, width=CRT_W, height=CRT_H,
                             bg=CRT_BG, highlightthickness=0)
        self.crt.pack(padx=3, pady=3)

        # Warm glow backdrop
        for i in range(CRT_H):
            warmth = int(6 * math.sin(math.pi * i / CRT_H))
            shade  = f"#{warmth:02x}{int(warmth * 0.45):02x}00"
            self.crt.create_line(0, i, CRT_W, i, fill=shade)

        # Fax metadata text
        ts = time.strftime("%Y-%m-%d  %H:%M:%S")
        rows = [
            (f"DATE/TIME: {ts}",              CRT_AMBER, 10, 14),
            ("FROM: +1(408)555-0192  XT-9000", CRT_DIM,  10, 32),
            ("TO:   LOCAL TERMINAL",            CRT_DIM,  10, 48),
            ("PAGE: 001   RES: FINE   ECM: ON", CRT_DIM,  10, 64),
        ]
        for text, colour, x, y in rows:
            self.crt.create_text(x + 1, y + 1, anchor="w", text=text,
                                 font=(self.mono_font, 9), fill=CRT_GLOW)
            self.crt.create_text(x, y, anchor="w", text=text,
                                 font=(self.mono_font, 9), fill=colour)

        # CRT scanlines
        for y in range(0, CRT_H, 2):
            self.crt.create_line(0, y, CRT_W, y,
                                 fill="#000000", stipple="gray25")

 
        # Power LED
        self.crt.create_oval(CRT_W - 13, CRT_H - 13,
                             CRT_W - 6,  CRT_H - 6,
                             fill="#ff5500", outline="#552200")

    # ─────────────────────────────────────────
    def _draw_paper_title(self):
        self.viewport.create_rectangle(
            self.paper_x + 8, 6,
            self.paper_x + PAPER_WIDTH - 8, 28,
            fill="#1a1208", outline="", tags="paper_content"
        )
        self.viewport.create_text(
            self.paper_x + PAPER_WIDTH // 2, 17,
            text="★  INCOMING  TRANSMISSION  ★",
            font=(self.mono_font, 8, "bold"), fill=PAPER_BG,
            tags="paper_content"
        )

    # ─────────────────────────────────────────
    def _add_paper_grain(self):
        for _ in range(700):
            x     = self.paper_x + random.randint(2, PAPER_WIDTH - 2)
            y     = random.randint(2, self.PAPER_H - 2)
            shade = random.choice(["#d0ccbc", "#c8c4b4", "#dedad0", "#ccc8b8"])
            self.viewport.create_rectangle(
                x, y, x + 1, y + 1,
                fill=shade, outline="", tags="paper_content"
            )

    def _draw_scanlines(self):
        for y in range(0, self.VP_H, 4):
            self.viewport.create_line(0, y, WIN_WIDTH, y,
                                      fill="#000000", width=1, stipple="gray25")

    def _draw_leds(self):
        self.led_canvas.delete("all")
        labels = ["PWR", "RX", "TX", "ERR"]
        states = [True, self.printing, False, False]
        colors = [LED_ON if s else LED_OFF for s in states]
        for i, (lbl, col) in enumerate(zip(labels, colors)):
            x = 12 + i * 44
            if col == LED_ON:
                self.led_canvas.create_oval(x - 8, 8, x + 8, 24,
                                            fill="#002211", outline="")
            self.led_canvas.create_oval(x - 5, 11, x + 5, 21,
                                        fill=col, outline="#001a0a")
            self.led_canvas.create_text(x, 30, text=lbl,
                                        font=("Courier", 6), fill="#2a2a2a")

    # ─────────────────────────────────────────
    #  COORDINATE HELPERS
    # ─────────────────────────────────────────
    def paper_to_view(self, y):
        return y - self.paper_y

    def _scroll_all(self, dy):
        self.viewport.move("paper_content", 0, -dy)
        self.viewport.move(self.paper,       0, -dy)
        self.viewport.move(self.paper_shadow, 0, -dy)

    # ─────────────────────────────────────────
    #  MAIN SEQUENCE
    # ─────────────────────────────────────────
    def _start_sequence(self):
        self.status_var.set("CONNECTING...")
        self.root.after(600, self._handshake)

    def _handshake(self):
        self.status_var.set("HANDSHAKING...")
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
        self.viewport.itemconfigure(self.scan_bar,  state="normal")
        self.viewport.itemconfigure(self.scan_glow, state="normal")
        self.scanning = True
        self._advance_scan()

    def _update_scan_bar_pos(self):
        vy = self.paper_to_view(self.scan_y)
        self.viewport.coords(self.scan_bar,
                             self.paper_x,             vy - 6,
                             self.paper_x + PAPER_WIDTH, vy)
        self.viewport.coords(self.scan_glow,
                             self.paper_x,             vy - 18,
                             self.paper_x + PAPER_WIDTH, vy + 4)

    def _advance_scan(self):
        if not self.scanning:
            return
        self.scan_y += SCAN_SPEED
        self._update_scan_bar_pos()

        vy = self.paper_to_view(self.scan_y)
        if vy > self.VP_H - 60:
            self.paper_y += FEED_SPEED
            self._scroll_all(FEED_SPEED)

        if self.scan_y >= self.text_y:
            self.scanning = False
            self._print_next_char()
        else:
            self.root.after(8, self._advance_scan)

    # ─────────────────────────────────────────
    #  TEXT PRINTING
    # ─────────────────────────────────────────
    def _print_next_char(self):
        if self.done:
            return
        total = len(self.lines)
        if self.current_line >= total:
            self._finish()
            return

        line = self.lines[self.current_line]

        if self.current_char == 0:
            self.line_item = self.viewport.create_text(
                self.text_x,
                self.paper_to_view(self.text_y),
                anchor="nw", text="",
                font=(self.mono_font, FONT_SIZE),
                fill=INK_COLOR, tags="paper_content"
            )
            if random.random() < 0.05:
                self._emit_noise()

        self.current_char += 1
        self.viewport.itemconfigure(self.line_item, text=line[:self.current_char])

        # Keep scan bar glued just below current text
        self.scan_y = self.text_y + 2
        self._update_scan_bar_pos()

        # Scroll paper if text is getting close to the bottom
        if self.paper_to_view(self.text_y) > self.VP_H - 60:
            scroll = FEED_SPEED * 2
            self.paper_y += scroll
            self._scroll_all(scroll)

        # Progress bar
        progress = ((self.current_line + self.current_char / max(len(line), 1))
                    / total)
        self.prog_canvas.coords(self.prog_bar, 0, 0,
                                int(300 * min(progress, 1.0)), 12)
        self.line_count_var.set(f"LINE: {self.current_line:04d}")

        if self.current_char >= len(line):
            # Line complete — advance to next
            self.current_char  = 0
            self.current_line += 1
            self.text_y       += FONT_SIZE + LINE_GAP + 4
            self.root.after(random.randint(30, 90), self._print_next_char)
        else:
            delay = CHAR_DELAY_MS + random.randint(-4, 8)
            self.root.after(max(4, delay), self._print_next_char)

    def _emit_noise(self):
        ox   = self.text_x + random.randint(0, 200)
        item = self.viewport.create_text(
            ox, self.paper_to_view(self.text_y),
            anchor="nw", text=random.choice(NOISE_CHARS),
            font=(self.mono_font, FONT_SIZE),
            fill=NOISE_COLOR, tags="paper_content"
        )
        self.root.after(80, lambda: self.viewport.delete(item))

    # ─────────────────────────────────────────
    #  FINISH
    # ─────────────────────────────────────────
    def _finish(self):
        self.done = True
        self.viewport.itemconfigure(self.scan_bar,  state="hidden")
        self.viewport.itemconfigure(self.scan_glow, state="hidden")

        cx = self.paper_x + PAPER_WIDTH // 2
        y0 = self.text_y + 10
        self.viewport.create_text(
            cx, self.paper_to_view(y0),
            text="─" * 76,
            font=(self.mono_font, 7), fill="#b0ac9c", tags="paper_content"
        )
        self.viewport.create_text(
            cx, self.paper_to_view(y0 + 14),
            text="END OF TRANSMISSION",
            font=(self.mono_font, 8, "bold"), fill=INK_COLOR,
            tags="paper_content"
        )
        self.viewport.create_text(
            cx, self.paper_to_view(y0 + 26),
            text=f"TOTAL LINES: {len(self.lines):04d}   STATUS: OK   ECM: PASS",
            font=(self.mono_font, 7), fill=INK_COLOR, tags="paper_content"
        )

        self.prog_canvas.coords(self.prog_bar, 0, 0, 300, 12)
        self.status_var.set("TRANSMISSION RECEIVED OK")
        self.printing = False
        self._draw_leds()
        self.line_count_var.set(f"LINE: {len(self.lines):04d}")
        self.root.title("FAX RECEIVED — OK")
        self._blink_done()

    def _blink_done(self):
        self.status_var.set(
            "TRANSMISSION RECEIVED OK" if self.blink_state else ""
        )
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

    WRAP  = 76
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

    FaxMachine(root, lines)

    root.bind("<Escape>", lambda e: root.destroy())
    root.bind("q",        lambda e: root.destroy())
    root.bind("Q",        lambda e: root.destroy())

    root.mainloop()


if __name__ == "__main__":
    main()