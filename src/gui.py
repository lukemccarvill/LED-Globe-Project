'''
minimal gui for project toggles and parameters
- uses Tkinter
- to add more toggles, add parameter in options and in SCHEMA

Run this script, and it will call upon main.py.
'''

desc = (
    "This program generates a world map divided into gores for a flexible PCB globe.\n"
    "It uses either a population density or nighttime light raster to distribute LEDs, "
    "and can draw outlines, LEDs, and other optional features."
)


from dataclasses import asdict
from main import Options
from typing import Optional
# from typing import Dict, List, Tuple

def get_options_gui(initial: Options) -> Options:
    try:
        import tkinter as tk
        from tkinter import ttk
    except Exception:
        return None # unless they hit "OK", everything finishes. 
    try:
        root = tk.Tk()
    except Exception:
        return None # unless they hit "OK", everything finishes. 
    
    root.title("LED Globe Options")
    root.resizable(False, False)

    frm = ttk.Frame(root, padding=16); frm.pack(fill="both", expand=True)

    desc_label = ttk.Label(
        frm,
        text=desc,
        justify="left",
        wraplength=420  # keeps the text nicely wrapped
    )
    desc_label.grid(row=0, column=0, sticky="w", pady=(0, 10))


    

    # Add/remove toggles here
    schema = [
        ("Draw gore outlines", "draw_gores"),
        ("Draw equator line", "draw_equator"),
        ("Draw countries", "draw_countries"),
        ("Draw LED markers", "draw_leds"),
        ("Use pre-edited GeoJSON (highly recommended True)", "use_edited_geojson"),
        ("Manual manipulation mode (highly recommended False)", "manual_manipulation"),
        ("Create coordinate spreadsheet for PCB manufacturing", "create_coords_for_manufact"),
        ("Use simplified countries", "use_simplified_countries"),
    ]

    bool_vars = {}
    row = 1
    for label, field in schema:
        v = tk.BooleanVar(value=getattr(initial, field))
        bool_vars[field] = v
        ttk.Checkbutton(frm, text=label, variable=v).grid(row=row, column=0, sticky="w", pady=2)
        row += 1

    # Separator (use grid)
    ttk.Separator(frm).grid(row=row, column=0, sticky="ew", pady=(10, 6))
    row += 1

    # Raster choice (radiobuttons on grid)
    ttk.Label(frm, text="Raster source:").grid(row=row, column=0, sticky="w", pady=(0, 4))
    row += 1

    raster_var = tk.StringVar(value=getattr(initial, "raster_choice", "population"))
    raster_row = ttk.Frame(frm)
    raster_row.grid(row=row, column=0, sticky="w")
    ttk.Radiobutton(raster_row, text="Population density", variable=raster_var, value="population").grid(row=0, column=0, padx=(0, 12))
    ttk.Radiobutton(raster_row, text="Nighttime lights",  variable=raster_var, value="nightlights").grid(row=0, column=1)
    row += 1

    # Buttons

    result = {"opts": None} # default is cancelled unless "OK" is pressed
    def on_ok():
        data = asdict(initial)
        for _, field in schema:
            data[field] = bool_vars[field].get()
        data["raster_choice"] = raster_var.get()
        result["opts"] = Options(**data)
        root.destroy()

    def on_cancel():
        result["opts"] = None
        root.destroy()

    btns = ttk.Frame(frm)
    btns.grid(row=row, column=0, sticky="e", pady=(12, 0))
    ttk.Button(btns, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(btns, text="OK", command=on_ok).grid(row=0, column=1)
    root.protocol("WM_DELETE_WINDOW", on_cancel) # X closes = cancel
    root.bind("<Escape>", lambda e: on_cancel())

    root.update_idletasks()
    w, h = 440, (len(schema) * 28) + 180
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    root.mainloop()
    return result["opts"]


if __name__ == "__main__":
    # Click “Run” on gui.py → choose toggles → runs the pipeline.
    opts = get_options_gui(Options())
    if opts is None:
        print("Run cancelled. Must click OK to begin run.")
    else:
        from main import run   # import here to avoid any chance of cycles
        run(opts)
