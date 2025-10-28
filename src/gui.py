'''
minimal gui for project toggles and parameters
- uses Tkinter
- to add more toggles, add parameter in options and in SCHEMA

'''

from dataclasses import dataclass, asdict
from typing import Dict, List, Tuple

# --- Defaults ---
@dataclass
class Options:
    draw_gores: bool = True
    draw_equator: bool = True
    # add more fields here later

# --- Toggle schema (label, field_name, default)

SCHEMA: List[Tuple[str, str, bool]] = [
    ("Draw gore outlines", "draw_gores", True),
    ("Draw equator line", "draw_equator", True),
    # add more toggles here later
]

def get_options_gui(initial: Options) -> Options:
    '''Show a small gui to set parameters. fall back to defautls if headless mode.'''
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        # (if tkinter not available)
        return initial
    
    # try to create a root window (may fail if headless)
    try:
        root = tk.Tk()

    except Exception:
        return initial
    
    root.title("LED Globe Options")
    root.resizable(False, False) # maybe change this later to be resizeable?

    frm = ttk.Frame(root, padding=16)
    frm.pack(fill="both", expand=True)

    # build controls from schema
    bool_vars: Dict[str, tk.BooleanVar] = {}
    for row, (label, field, default) in enumerate(SCHEMA):
        # use existing value from initial if present; else schema default
        start_val = getattr(initial, field, default)
        var = tk.BooleanVar(value=bool(start_val))
        bool_vars[field]= var
        ttk.Checkbutton(frm, text=label, variable=var).grid(row=row, column=0, sticky='w', pady=2)

    btns = ttk.Frame(frm)
    btns.grid(row=len(SCHEMA), column=0, pady=(12,0), sticky="e")

    result = {"options": initial}

    def on_ok():
        # collect values back into an options instance
        data = asdict(initial)
        for _, field, _ in SCHEMA:
            data[field] = bool_vars[field].get()
        result["options"] = Options(**data)
        root.destroy()

    def on_cancel():
        # keep initial values
        root.destroy()

    # defining buttons in gui
    ttk.Button(btns, text="Cancel", command=on_cancel).pack(side="right", padx=(0,8))
    ttk.Button(btns, text="OK", command=on_ok).pack(side="right")

    # centre window
    root.update_idletasks()
    w,h = 360, (len(SCHEMA)*28) + 100
    sw,sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h} + {(sw-w)//w}+{(sh-h)//2}") # window width by height (in pixels) + distance from left edge + distance from top edge.
                                                        # // is integer division (no decimals)
    
    root.mainloop()
    return result["options"]

def main():
    # defaults; can tweak
    defaults = Options( 
        draw_gores = True,
        draw_equator = True,
    )
    opts = get_options_gui(defaults)

    print("Selected options:")
    for k, v in asdict(opts).items():
        print(f"  {k}: {v}")

    # stuff to persist here? toml?

if __name__ == "__main__": # only run the main() function if this file is executed directly, not when it's imported. 
    main()


