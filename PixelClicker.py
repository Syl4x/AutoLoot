import ctypes
from ctypes import wintypes
import os
import sys
import colorsys
import importlib
import importlib.util
import subprocess
import threading
import time
import random
import pathlib


# ---------------- Auto install (missing libraries) ----------------
# import name -> pip package name
REQUIRED_PACKAGES = {
    "pyautogui": "pyautogui",
    "keyboard": "keyboard",
    "pygetwindow": "pygetwindow",
    "mss": "mss",
    "numpy": "numpy",
    "PIL": "pillow",
}


def ensure_packages():
    """Script eka run karanna one libraries nathnam, auto check karala pip eken install karanawa"""
    missing = [pkg for mod, pkg in REQUIRED_PACKAGES.items() if importlib.util.find_spec(mod) is None]
    if missing:
        print("PixelClicker: installing missing libraries ->", ", ".join(missing))
        print("(Internet eka one. Podi welawak inna...)\n")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
        except Exception:
            try:  # pip ma nathnam eka hadala ayeth try karanawa
                subprocess.check_call([sys.executable, "-m", "ensurepip", "--upgrade"])
                subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])
            except Exception as e:
                print(f"\nAuto install wada kale na: {e}")
                print("Manual install karanna:  pip install " + " ".join(missing))
                input("Enter ebuwama close wenawa...")
                sys.exit(1)
        importlib.invalidate_caches()
        print("\nInstall iwarai. Script eka start wenawa...\n")

    if importlib.util.find_spec("tkinter") is None:
        print("tkinter nathi. Python ayeth install karanna (installer eke 'tcl/tk and IDLE' tick karanna).")
        input("Enter ebuwama close wenawa...")
        sys.exit(1)


ensure_packages()

import mss
import numpy as np
import pyautogui
import keyboard
import pygetwindow as gw
import tkinter as tk

# ==================== CONFIGURATION ====================
GAME_WINDOW_TITLE = "Albion Online Client"

TOLERANCE = 30        # color eka R,G,B walin meka wenas unath match wenawa
SCAN_WIDTH = 80       # detector box eke width
SCAN_HEIGHT = 30      # detector box eke height
SCAN_MARGIN = 3       # box eke border eken pixel 3 k athulin thamai scan wenne

SCAN_INTERVAL = 0.02    # scan 2 k athara welawa (seconds). Lag nam wadi karanna (0.03, 0.05)
WINDOW_REFRESH = 0.25   # game window eka hoyanne meka-wath welawakata parakak (seconds)

# Detector 3 k. Click wenne Detector 1 color eka hamba una thanata (3 ma match unama).
DETECTORS = [
    {"x": 200, "y": 200, "color": (255, 0, 0)},
    {"x": 300, "y": 200, "color": (0, 255, 0)},
    {"x": 400, "y": 200, "color": (0, 0, 255)},
]
OVERLAY_COLORS = ["green", "orange", "cyan"]  # box 1, 2, 3 walata colors

# ---------- Click eke delays (seconds) ----------
LOCK_MOUSE = True                 # True = click eka wena welawe oyage mouse eka lock wenawa
DELAY_BEFORE_MOVE = (0.01, 0.04)  # move wenna kalin (random: min, max)
DELAY_AFTER_MOVE = 0.02           # position ekata giya passe, press karanna kalin
DELAY_HOLD = 0.03                 # press karala release karanakan inna welawa
DELAY_AFTER_RELEASE = 0.02        # release unata passe, mouse eka free karanna kalin
DELAY_AFTER_CLICK = 0.15          # click eka iwara unata passe ayeth scan karanna kalin

# Hotkeys
TOGGLE_RUN_KEY = 'f3'      # Start / Pause
TOGGLE_VISUAL_KEY = 'f4'   # Boxes show/hide (boxes pennanakota witharai F5-F8 wada karanne)
CALIBRATE_POS_KEY = 'f5'   # Lock position
SELECT_KEY = 'f6'          # Change detector (1 -> 2 -> 3)
INPUT_COLOR_KEY = 'f7'     # Type RGB
PICK_COLOR_KEY = 'f8'      # Pick color under mouse
# =======================================================

APP_NAME = "PixelClicker"

SAVE_DIR = pathlib.Path.home() / ".game_clicker_config"
SAVE_DIR.mkdir(exist_ok=True)
CONFIG_FILE_PATH = SAVE_DIR / "saved_config_3det.txt"

user32 = ctypes.windll.user32
ctypes.windll.kernel32.SetConsoleTitleW(APP_NAME)

is_running = False
show_overlay = False
typing = False                 # RGB type karana welawe screen eka redraw wenna epa
pyautogui.PAUSE = 0
selected = 0
message = ""                   # kalin kala dewal wala podi pennuma
egg_on = False                 # F3+F4 ekapara ebuwama "Powered by Syl4x" pennanawa
last_combo = 0.0               # F3+F4 kala aniyama welawa
vt_ok = False                  # console eka color (ANSI) support karanawada
actual_pos = [(0, 0), (0, 0), (0, 0)]
render_lock = threading.Lock()


# ---------------- Screen (console) ----------------
EGG_PREFIX = f"{APP_NAME} | Powered by "
EGG_NAME = "syl4x."


def enable_vt():
    """Console eke colors (ANSI) on karanawa"""
    global vt_ok
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = wintypes.DWORD()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            vt_ok = bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))
    except Exception:
        vt_ok = False


def egg_name(t):
    """'Syl4x' akuru hama ekakama wenama color ekak (rainbow wage maru wenawa)"""
    if not vt_ok:
        return EGG_NAME
    out = ""
    for i, ch in enumerate(EGG_NAME):
        r, g, b = colorsys.hsv_to_rgb((t * 0.4 + i * 0.13) % 1.0, 0.75, 1.0)
        out += f"\033[38;2;{int(r * 255)};{int(g * 255)};{int(b * 255)}m{ch}"
    return out + "\033[0m"


def egg_animation():
    """'Syl4x' eke colors maru karanna thread eka (egg ON nam witharai)"""
    start = time.time()
    while True:
        time.sleep(0.08)
        if egg_on and vt_ok and not render_lock.locked():
            with render_lock:
                if egg_on:
                    col = len(EGG_PREFIX) + 1
                    # cursor eka save karala 1 weni line eke Syl4x thanata gihin color karala ayeth cursor eka restore
                    sys.stdout.write(f"\0337\033[1;{col}H{egg_name(time.time() - start)}\0338")
                    sys.stdout.flush()


def render():
    """Console eka clear karala piliwelata dashboard eka ayeth pennanawa"""
    if typing:
        return
    with render_lock:
        enable_vt()
        os.system("cls")
        if egg_on:
            print(EGG_PREFIX + egg_name(0.0))  # PixelClicker | Powered by Syl4x (ekama line ekak)
        else:
            print(APP_NAME)
        print()
        for i, d in enumerate(DETECTORS):
            mark = ">>" if (show_overlay and i == selected) else "  "
            print(f"{mark} Detector {i + 1}: X={d['x']}, Y={d['y']}, Color={d['color']}")
        print()
        print("F3 Start/Pause")
        print("F4 Show/Hide Boxes")
        print("F5 Lock position")
        print("F6 Change detector")
        print("F7 Type RGB")
        print("F8 Pick color under mouse")
        print()
        run_text = "ACTIVE" if is_running else "PAUSED"
        box_text = "SHOWN (F5-F8 on)" if show_overlay else "HIDDEN (F5-F8 off)"
        print(f"Clicker: {run_text} | Boxes: {box_text}")
        if message:
            print(message)


def set_message(text):
    global message
    message = text
    render()


# ---------------- Mouse lock (Administrator one na) ----------------
def lock_mouse_at(x, y):
    """Cursor eka (x, y) pixel ekata confine karanawa, ethakota physical mouse eken move karanna ba"""
    rect = wintypes.RECT(int(x), int(y), int(x) + 1, int(y) + 1)
    user32.ClipCursor(ctypes.byref(rect))


def unlock_mouse():
    user32.ClipCursor(None)


def perform_click(x, y):
    """Move -> press -> release (mouse lock wela) -> free -> original thanata"""
    orig_x, orig_y = pyautogui.position()
    try:
        time.sleep(random.uniform(*DELAY_BEFORE_MOVE))
        pyautogui.moveTo(x, y)
        if LOCK_MOUSE:
            lock_mouse_at(x, y)
        time.sleep(DELAY_AFTER_MOVE)
        pyautogui.mouseDown()
        time.sleep(DELAY_HOLD)
        pyautogui.mouseUp()
        time.sleep(DELAY_AFTER_RELEASE)
        unlock_mouse()  # release unata passe thamai control eka denne
    finally:
        unlock_mouse()  # error ekak unath mouse eka lock wela nathi wenna
        pyautogui.moveTo(orig_x, orig_y)
    time.sleep(DELAY_AFTER_CLICK)


# ---------------- Config ----------------
def load_saved_data():
    global message
    if not CONFIG_FILE_PATH.exists():
        return
    try:
        lines = CONFIG_FILE_PATH.read_text().splitlines()
        for i in range(3):
            parts = list(map(int, lines[i].split(',')))
            x, y, r, g, b = parts[:5]
            DETECTORS[i] = {"x": x, "y": y, "color": (r, g, b)}
    except Exception as e:
        message = f"Error reading config: {e}. Using default values."


def save_data_safely():
    try:
        with open(CONFIG_FILE_PATH, "w") as f:
            for d in DETECTORS:
                r, g, b = d["color"]
                f.write(f"{d['x']},{d['y']},{r},{g},{b}\n")
    except Exception as e:
        set_message(f"Save error: {e}")


# ---------------- Hotkey actions ----------------
def toggle_script():
    global is_running
    is_running = not is_running
    set_message("")


def toggle_visual():
    global show_overlay
    show_overlay = not show_overlay
    set_message("")


def select_next():
    global selected
    selected = (selected + 1) % 3
    set_message("")


def calibrate_position():
    """Mouse eka thiyena thanata SELECTED detector eka lock karanawa"""
    try:
        windows = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
        if not windows:
            set_message(f"Window '{GAME_WINDOW_TITLE}' not found!")
            return
        game_win = windows[0]
        mouse_x, mouse_y = pyautogui.position()
        d = DETECTORS[selected]
        d["x"] = max(0, mouse_x - game_win.left - (SCAN_WIDTH // 2))
        d["y"] = max(0, mouse_y - game_win.top - (SCAN_HEIGHT // 2))
        actual_pos[selected] = (game_win.left + d["x"], game_win.top + d["y"])
        save_data_safely()
        set_message(f"Detector {selected + 1} position locked")
    except Exception as e:
        set_message(f"Position error: {e}")


def _input_color_worker():
    global is_running, typing
    was_running = is_running
    is_running = False
    idx = selected
    render()
    typing = True
    try:
        color_str = input(f"Detector {idx + 1} color (R,G,B): ")
        parts = [int(x.strip()) for x in color_str.split(',')]
        if len(parts) == 3 and all(0 <= x <= 255 for x in parts):
            DETECTORS[idx]["color"] = tuple(parts)
            save_data_safely()
            result = f"Detector {idx + 1} color set"
        else:
            result = "Invalid format! Example: 255,0,0"
    except Exception as e:
        result = f"Error: {e}"
    typing = False
    is_running = was_running
    set_message(result)


def input_color():
    threading.Thread(target=_input_color_worker, daemon=True).start()


def pick_color_under_mouse():
    """Mouse eka thiyena pixel eke color eka SELECTED detector ekata set karanawa"""
    x, y = pyautogui.position()
    r, g, b = pyautogui.pixel(x, y)[:3]
    DETECTORS[selected]["color"] = (r, g, b)
    save_data_safely()
    set_message(f"Detector {selected + 1} color picked: ({r}, {g}, {b})")


def edit_only(fn):
    """F5-F8 wada karanne boxes pennanakota (F4 ON) witharai"""
    def wrapper():
        if show_overlay and not typing:
            fn()
    return wrapper


def combo_egg():
    """F3 + F4 ekapara ebuwama 'Powered by Syl4x' pennanawa / hide karanawa"""
    global egg_on, last_combo
    now = time.time()
    if now - last_combo < 0.6:  # key eka thiyagena inna welawe ayeth ayeth wada nowenna
        return
    last_combo = now
    egg_on = not egg_on
    render()


def deferred(fn):
    """F3 / F4 eka podi welawak (0.15s) inna, F3+F4 ekapara ebuwe nathnam witharai wada karanne"""
    def wrapper():
        def run():
            if time.time() - last_combo > 0.3:
                fn()
        threading.Timer(0.15, run).start()
    return wrapper


keyboard.add_hotkey(TOGGLE_RUN_KEY, deferred(toggle_script))
keyboard.add_hotkey(TOGGLE_VISUAL_KEY, deferred(toggle_visual))
keyboard.add_hotkey(f"{TOGGLE_RUN_KEY}+{TOGGLE_VISUAL_KEY}", combo_egg)
keyboard.add_hotkey(CALIBRATE_POS_KEY, edit_only(calibrate_position))
keyboard.add_hotkey(SELECT_KEY, edit_only(select_next))
keyboard.add_hotkey(INPUT_COLOR_KEY, edit_only(input_color))
keyboard.add_hotkey(PICK_COLOR_KEY, edit_only(pick_color_under_mouse))


# ---------------- Overlay ----------------
def create_overlay():
    root = tk.Tk()
    root.withdraw()
    boxes = []
    for i in range(3):
        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.wm_attributes("-topmost", True, "-transparentcolor", "white")
        win.config(bg="white")
        canvas = tk.Canvas(win, width=SCAN_WIDTH, height=SCAN_HEIGHT, bg="white", highlightthickness=0)
        canvas.pack()
        canvas.create_rectangle(0, 0, SCAN_WIDTH, SCAN_HEIGHT, outline=OVERLAY_COLORS[i], width=3)
        win.withdraw()
        boxes.append(win)

    last_geo = [None, None, None]

    def update_position():
        for i, win in enumerate(boxes):
            ax, ay = actual_pos[i]
            geo = f"{SCAN_WIDTH}x{SCAN_HEIGHT}+{ax}+{ay}" if (show_overlay and ax > 0 and ay > 0) else None
            if geo != last_geo[i]:  # wenas unoth witharai update karanne (lag adu karanna)
                last_geo[i] = geo
                if geo:
                    win.deiconify()
                    win.geometry(geo)
                else:
                    win.withdraw()
        root.after(50, update_position)

    root.after(50, update_position)
    root.mainloop()


# ---------------- Scanning ----------------
def find_color(sct, pos, color):
    """
    Box eka athule (border eken SCAN_MARGIN pixel k athulin) color eka hoyanawa.
    Scan wena podi area eka witharai capture karanne (mss).
    Hamba unoth click position (match una pixels walin madhyaya), nathnam None.
    """
    left, top = pos[0] + SCAN_MARGIN, pos[1] + SCAN_MARGIN
    width, height = SCAN_WIDTH - 2 * SCAN_MARGIN, SCAN_HEIGHT - 2 * SCAN_MARGIN

    img = sct.grab({"left": left, "top": top, "width": width, "height": height})
    arr = np.frombuffer(img.bgra, dtype=np.uint8).reshape(img.height, img.width, 4)
    rgb = arr[:, :, 2::-1].astype(np.int16)  # B,G,R,A -> R,G,B

    diff = np.abs(rgb - np.array(color, dtype=np.int16)).max(axis=2)
    ys, xs = np.nonzero(diff <= TOLERANCE)
    if xs.size == 0:
        return None
    return (left + int(xs.mean()), top + int(ys.mean()))


def scanning_loop():
    game_win = None
    last_refresh = 0.0

    try:
        # aluth mss version ekedi mss.MSS, palaya ewage mss.mss
        mss_class = getattr(mss, "MSS", None) or mss.mss
        # mss object eka scan karana thread ekatama create karanna oni
        with mss_class() as sct:
            while True:
                now = time.time()
                if now - last_refresh >= WINDOW_REFRESH:
                    last_refresh = now
                    windows = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
                    if windows:
                        game_win = windows[0]
                        for i, d in enumerate(DETECTORS):
                            actual_pos[i] = (max(0, game_win.left + d["x"]), max(0, game_win.top + d["y"]))
                    else:
                        game_win = None
                        for i in range(3):
                            actual_pos[i] = (0, 0)

                if game_win is None:
                    time.sleep(0.5)
                    last_refresh = 0.0
                    continue

                if is_running:
                    try:
                        hits = [find_color(sct, actual_pos[i], DETECTORS[i]["color"]) for i in range(3)]
                        if all(h is not None for h in hits):
                            hit1 = hits[0]  # Detector 1 color eka hamba una thana
                            perform_click(hit1[0], hit1[1])
                    except Exception as e:
                        unlock_mouse()
                        set_message(f"Scan error: {e}")
                        time.sleep(0.5)

                time.sleep(SCAN_INTERVAL)
    finally:
        unlock_mouse()


load_saved_data()
render()
threading.Thread(target=scanning_loop, daemon=True).start()
threading.Thread(target=egg_animation, daemon=True).start()
create_overlay()
unlock_mouse()
