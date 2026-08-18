import functools
import json
import os
import subprocess
import sys
import threading
import uuid
from datetime import datetime
from tkinter import *

import get_user
from _version import __version__

def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(app_dir(), "poor_man.json")
with open(CONFIG_PATH) as f:
    _config = json.load(f)
ROOT_DIR = _config["poor_man_message_queue_root"]
STATUS_PATH = os.path.join(ROOT_DIR, "status.json")
LAST_MODIFIED = None

CURRENT_USER = get_user.get_display_name()

root = Tk()
title = f"Lab Tools {__version__}"
root.title(title)

topmost_enabled = True

def reassert_topmost():
    if topmost_enabled:
        root.attributes("-topmost", False)
        root.attributes("-topmost", True)
    root.after(3000, reassert_topmost)

def snap_to_bottom_right():
    root.update_idletasks()

    window_width = root.winfo_reqwidth()
    window_height = root.winfo_reqheight()

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = screen_width - window_width - 10
    y = screen_height - window_height - 50

    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

def start_drag(event):
    # Calculate the exact distance between the mouse pointer and the top-left edge of the window
    root._drag_offset_x = root.winfo_pointerx() - root.winfo_x()
    root._drag_offset_y = root.winfo_pointery() - root.winfo_y()

def stop_drag(event):
    if hasattr(root, '_drag_offset_x'): del root._drag_offset_x
    if hasattr(root, '_drag_offset_y'): del root._drag_offset_y

def do_drag(event):
    x = root.winfo_pointerx() - root._drag_offset_x
    y = root.winfo_pointery() - root._drag_offset_y
    root.geometry(f"+{x}+{y}")

def run_background_command(args):
    def _run():
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        result = subprocess.run(args, capture_output=True, text=True, creationflags=creationflags)
        print((result.stdout or result.stderr).strip())
    threading.Thread(target=_run, daemon=True).start()

def kill_all_rdp():
    if not sys.platform.startswith("win32"):
        print("Kill All RDP: only supported on Windows")
        return
    run_background_command(["taskkill", "/IM", "mstsc.exe", "/F"])

def toggle_topmost():
    global topmost_enabled
    topmost_enabled = not topmost_enabled
    root.attributes("-topmost", topmost_enabled)
    topmost_btn.config(text=" 📌 Stay on Top: ON " if topmost_enabled else " 📌 Stay on Top: OFF ")

title_bar = Frame(root, bg="#2e2e2e", height=30)
title_bar.grid(row=0, column=0, columnspan=6, sticky="ew")

title_bar.bind("<ButtonPress-1>", start_drag)
title_bar.bind("<ButtonRelease-1>", stop_drag)
title_bar.bind("<B1-Motion>", do_drag)

title_label = Label(title_bar, text=f"  {title}", font=("Arial", 10, "bold"), fg="white", bg="#2e2e2e")
title_label.pack(side="left", pady=5)

close_btn = Button(title_bar, text=" ✕ ", command=root.destroy, bg="#2e2e2e", fg="white", bd=0, highlightthickness=0, activebackground="red", activeforeground="white")
close_btn.pack(side="right", fill="y", padx=2)

reset_btn = Button(title_bar, text=" 🔄 Reset ", command=snap_to_bottom_right, bg="#2e2e2e", fg="white", bd=0, highlightthickness=0, activebackground="#4a4a4a", activeforeground="white")
reset_btn.pack(side="right", fill="y", padx=2)

kill_rdp_btn = Button(title_bar, text=" 💀 Kill All RDP ", command=kill_all_rdp, bg="#2e2e2e", fg="white", bd=0, highlightthickness=0, activebackground="#4a4a4a", activeforeground="white")
kill_rdp_btn.pack(side="right", fill="y", padx=2)

topmost_btn = Button(title_bar, text=" 📌 Stay on Top: ON ", command=toggle_topmost, bg="#2e2e2e", fg="white", bd=0, highlightthickness=0, activebackground="#4a4a4a", activeforeground="white")
topmost_btn.pack(side="right", fill="y", padx=2)

root.overrideredirect(True)

lab_widgets = {}

placeholder_label = Label(root, text="Waiting for server...", anchor="w")
placeholder_label.grid(row=1, column=0, padx=(15, 15), pady=8, sticky="w")

def load_status():
    if not os.path.exists(STATUS_PATH):
        return None

    with open(STATUS_PATH) as f:
        return json.load(f)

def write_request(lab, action):
    request = {
        "action": action,
        "user": CURRENT_USER,
        "lab": lab,
        "timestamp": datetime.now().isoformat(),
    }
    uid = uuid.uuid4().hex
    tmp_path = os.path.join(ROOT_DIR, f".req_{uid}.tmp")
    final_path = os.path.join(ROOT_DIR, f"req_{uid}.json")
    with open(tmp_path, "w") as f:
        json.dump(request, f)
    os.replace(tmp_path, final_path)

def handle_click(lab, action, button):
    button.config(state="disabled")
    threading.Thread(target=write_request, args=(lab, action), daemon=True).start()

AVAILABLE_BG = "#2e7d32"
OCCUPIED_BG = "#c62828"

def build_lab_widgets(status):
    placeholder_label.grid_forget()
    for i, lab in enumerate(sorted(status)):
        name_label = Label(root, text=lab, font=("Arial", 10, "bold"), fg="white")
        name_label.grid(row=1, column=i, padx=(15, 15), pady=(8, 0), sticky="ew")

        occupant_label = Label(root, anchor="center")
        occupant_label.grid(row=2, column=i, padx=(15, 15), pady=(0, 4), sticky="ew")

        button = Button(root)
        button.grid(row=3, column=i, padx=(15, 15), pady=(0, 8), sticky="ew")

        lab_widgets[lab] = (name_label, occupant_label, button)

    update_lab_widgets(status)
    snap_to_bottom_right()

def update_lab_widgets(status):
    for lab, (name_label, occupant_label, button) in lab_widgets.items():
        occupant = status.get(lab)

        if occupant is None:
            name_label.config(bg=AVAILABLE_BG)
            occupant_label.config(text="free")
            button.config(text="Check Out", state="normal",
                           command=functools.partial(handle_click, lab, "checkout", button))
        elif occupant == CURRENT_USER:
            name_label.config(bg=OCCUPIED_BG)
            occupant_label.config(text=occupant)
            button.config(text="Release", state="normal",
                           command=functools.partial(handle_click, lab, "release", button))
        else:
            name_label.config(bg=OCCUPIED_BG)
            occupant_label.config(text=occupant)
            button.config(text="Occupied", state="disabled")

def refresh_status():
    global LAST_MODIFIED

    try:
        modified = os.path.getmtime(STATUS_PATH) if os.path.exists(STATUS_PATH) else None
        if modified != LAST_MODIFIED:
            LAST_MODIFIED = modified
            status = load_status()
            if status is not None:
                if not lab_widgets:
                    build_lab_widgets(status)
                else:
                    update_lab_widgets(status)
    except Exception as e:
        print(f"refresh_status failed: {e}")
    finally:
        root.after(3000, refresh_status)


refresh_status()
snap_to_bottom_right()
reassert_topmost()

root.mainloop()
