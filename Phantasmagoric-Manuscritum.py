#!/usr/bin/env python3
"""
PHANTASMAGORIC MANUSCRIPTUM v1.0
Retro terminal editor with boot sequence & fax transmission

USAGE:
    python Phantasmagoric-Manuscritum.py [filename]

MODES:
    NORMAL  → default; navigate with arrow keys
    INSERT  → press [i] to type text
    COMMAND → press [:] to enter commands

COMMANDS:
    :open <file>   :save [file]   :quit   :q!   :new
    :goto <n>      :find <text>   :wq     :help
    :print <file>  → Send file to fax machine (python3 Faxprint.py <file>)
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
import subprocess

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
    print("\n  [!] Missing dependencies. Install them with the script provided for your respective system\n")
 
    sys.exit(1)

console = Console()

# ══════════════════════════════════════════════════════════════════════════════
#  RETRO COLOR SCHEME (Amber/Green Phosphor)
# ══════════════════════════════════════════════════════════════════════════════
RETRO_AMBER = "#ff9900"
RETRO_GREEN = "#00ff00"
RETRO_DIM = "#886600"


# ══════════════════════════════════════════════════════════════════════════════
#  BOOT SEQUENCE
# ══════════════════════════════════════════════════════════════════════════════

_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo")
with open(_logo_path, "r") as _f:
    LOGO_ASCII = _f.read()


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
    """Retro-styled boot sequence."""
    boot_start = time.time()
    sysinfo    = _get_sysinfo()
    boot_log   = []  # Collect boot messages

    console.clear()

    # LOGO
    console.print(f"[{RETRO_AMBER}]{LOGO_ASCII}[/{RETRO_AMBER}]")
    console.print()

    # FIRMWARE HEADER (updated to Mulberry-Systems)
    console.print(
        f"[bold {RETRO_AMBER}]Mulberry-Systems UEFI Firmware v2.8.4  "
        f"Copyright © 2004-2026  Mulberry-Systems[/bold {RETRO_AMBER}]"
    )
    boot_log.append(f"Mulberry-Systems UEFI Firmware v2.8.4  Copyright © 2004-2026")
    
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
        ("[    0.000000] Linux MulberryOS kernel 6.8.0-retro #1 SMP",         RETRO_AMBER,    0.05),
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
    time.sleep(0.8)

    console.clear()
    console.print(f"[bold {RETRO_GREEN}]✓  EDITOR READY  —  Launching interface...[/bold {RETRO_GREEN}]\n")
    time.sleep(0.5)

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

    def get_current_filepath(self) -> str:
        return self.filepath


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

    def _print_file(self, filepath: str):
        """Launch faxprint.py with the specified file."""
        if not filepath:
            self.message = "No file specified. Use: :print <filename>"
            self.msg_type = "error"
            return
        
        # Expand ~ if present
        filepath = os.path.expanduser(filepath)
        
        if not os.path.isfile(filepath):
            self.message = f"File not found: {filepath}"
            self.msg_type = "error"
            return
       

    def render(self):
        self.scr.erase()
        h, w = self.term_h, self.term_w

        # LOGO (4 lines) - updated to Mulberry-Systems
        logo_lines = [
            "╔═══════════════════════════════════════════════════════════════════════════╗",
            "║  PHANTASMAGORIC MANUSCRIPTUM v1.0  —  Mulberry-Systems (2004-2026)        ║",
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

        elif verb in ("p", "print"):
            # Print command: sends file to fax machine
            if not arg:
                # If no argument, try to print current buffer's file
                current_file = self.buf.get_current_filepath()
                if current_file:
                    self._print_file(current_file)
                else:
                    self.message = "Usage:  :print <filename>  (or save current file first)"
                    self.msg_type = "error"
            else:
                self._print_file(arg)

        elif verb in ("h", "help", "?"):
            self.message = (
                ":open <f>  :save [f]  :quit  :q!  :wq  :new  "
                ":goto <n>  :find <t>  :print <f>  |  i=INSERT  ESC=NORMAL  :=COMMAND"
            )
            self.msg_type = "info"

        else:
            self.message  = f"Unknown command '{verb}'.  Try  :help"
            self.msg_type = "error"

    def _print_file(self, filepath: str):
        """Launch faxprint.py with the specified file."""
        if not filepath:
            self.message = "No file specified. Use: :print <filename>"
            self.msg_type = "error"
            return
        
        # Expand ~ if present
        filepath = os.path.expanduser(filepath)
        
        if not os.path.isfile(filepath):
            self.message = f"File not found: {filepath}"
            self.msg_type = "error"
            return
        
        try:
            # Launch faxprint.py in background
            subprocess.Popen(
                ["python3", "Faxprint.py", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
            self.message = f"Fax transmission started: {os.path.basename(filepath)}"
            self.msg_type = "success"
        except Exception as e:
            self.message = f"Failed to launch fax: {e}"
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

    # 1. Boot sequence
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