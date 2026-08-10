import functools
import getpass
import json
import os
import sys
import uuid
from datetime import datetime
from tkinter import *
from tkinter import ttk

def app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

CONFIG_PATH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(app_dir(), "poor_man.json")
with open(CONFIG_PATH) as f:
    _config = json.load(f)
ROOT_DIR = _config["poor_man_message_queue_root"]

CURRENT_USER = getpass.getuser()

root = Tk()
title = "Lab Tools"
root.title(title)
root.attributes("-topmost", True)

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

def kill_all_rdp():
    print("Kill All RDP: not yet implemented")

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

root.overrideredirect(True)

lab_widgets = {}

placeholder_label = Label(root, text="Waiting for server...", anchor="w")
placeholder_label.grid(row=1, column=0, padx=(15, 15), pady=8, sticky="w")

def load_status():
    status_path = os.path.join(ROOT_DIR, "status.json")
    if not os.path.exists(status_path):
        return None
    with open(status_path) as f:
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
    write_request(lab, action)

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
    try:
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

root.mainloop()
