from tkinter import *
from tkinter import ttk

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

title_bar = Frame(root, bg="#2e2e2e", height=30)
title_bar.grid(row=0, column=0, columnspan=5, sticky="ew")

title_bar.bind("<ButtonPress-1>", start_drag)
title_bar.bind("<ButtonRelease-1>", stop_drag)
title_bar.bind("<B1-Motion>", do_drag)

title_label = Label(title_bar, text=f"  {title}", font=("Arial", 10, "bold"), fg="white", bg="#2e2e2e")
title_label.pack(side="left", pady=5)

close_btn = Button(title_bar, text=" ✕ ", command=root.destroy, bg="#2e2e2e", fg="white", bd=0, activebackground="red", activeforeground="white")
close_btn.pack(side="right", fill="y", padx=2)

reset_btn = Button(title_bar, text=" 🔄 Reset ", command=snap_to_bottom_right, bg="#2e2e2e", fg="white", bd=0, activebackground="#4a4a4a", activeforeground="white")
reset_btn.pack(side="right", fill="y", padx=2)

root.overrideredirect(True)

for i in range(5):
    label = Label(root, text=f"Options {i+1}", anchor="w")
    label.grid(row=1, column=i, padx=(15,5), pady=8, sticky="w")

    button = Button(root, text=f"Action {i+1}")
    button.grid(row=2, column=i, padx=(5,15), pady=8, sticky="e")

snap_to_bottom_right()

root.mainloop()
