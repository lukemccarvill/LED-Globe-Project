'''
Run this script, and it will call upon main.py.
- to add more toggles, add parameter in options and in SCHEMA
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
import os, re
from PIL import Image, ImageTk
import re


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
    
    # container with 2 columns: left (options), right (image)
    container = ttk.Frame(root, padding=12)
    container.grid(row=0, column=0, sticky="nsew")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    container.columnconfigure(0, weight=1)  # left column (options)
    container.columnconfigure(1, weight=1)  # right column (image)
    container.rowconfigure(1, weight=1)     # content row stretches

    desc_label = ttk.Label(container, text=desc, justify="left", wraplength=600)
    desc_label.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

    # left column: options (uses grid)
    frm = ttk.Frame(container)
    frm.grid(row=1, column=0, sticky="n", padx=(0, 0))

    # Add/remove toggles here
    schema = [
        ("Draw gore outlines", "draw_gores"),
        ("Draw equator line", "draw_equator"),
        ("Draw countries", "draw_countries"),
        ("Draw LED markers", "draw_leds"),
        ("Use pre-edited GeoJSON (recommended True)", "use_edited_geojson"), # deprecated?
        ("Manual manipulation mode (recommended False)", "manual_manipulation"), # deprecated?
        ("Create coordinate spreadsheet for PCB manufacturing", "create_coords_for_manufact"),
        ("Use simplified countries", "use_simplified_countries"),
    ]

    bool_vars = {}
    row = 0
    for label, field in schema:
        v = tk.BooleanVar(value=getattr(initial, field))
        bool_vars[field] = v
        ttk.Checkbutton(frm, text=label, variable=v).grid(row=row, column=0, sticky="w", pady=2)
        row += 1

    # Separator (use grid)
    ttk.Separator(frm).grid(row=row, column=0, sticky="ew", pady=(10, 6))
    row += 1

    # raster stuff:
    project_root = os.path.dirname(os.path.dirname(__file__))
    raster_dir = os.path.join(project_root, "data", "rasters")

    # helper to detect years present for each raster family
    def detect_years(pattern: re.Pattern) -> list[int]:
        years = set()
        if os.path.isdir(raster_dir):
            for f in os.listdir(raster_dir):
                m = pattern.search(f)
                if m:
                    years.add(int(m.group(1)))
        # Sort ascending; if empty, fall back to canonical 1975..2025 step 5
        if years:
            return sorted(years)
        return list(range(1975, 2026, 5))

    # Compile patterns for the three “yearful” families
    pop_pat = re.compile(r"GHS_POP_E(\d{4})_30arcmin\.tif$", re.IGNORECASE)
    ghs_vol_pat = re.compile(r"GHS_BUILT_V_E(\d{4})_30arcmin\.tif$", re.IGNORECASE)
    ghs_surf_pat = re.compile(r"GHS_BUILT_S_E(\d{4})_30arcmin\.tif$", re.IGNORECASE)

    years_by_key = {
        "population": detect_years(pop_pat),
        "ghs_volume": detect_years(ghs_vol_pat),
        "ghs_surface": detect_years(ghs_surf_pat),
        # nightlights is fixed to 2023
    }

    # ttk.Separator(frm).grid(row=row, column=0, sticky="ew", pady=(10, 6))
    # row += 1

    ttk.Label(frm, text="Raster source:").grid(row=row, column=0, sticky="w", pady=(0, 4))
    row += 1

    raster_var = tk.StringVar(value=getattr(initial, "raster_choice", "population"))
    raster_row = ttk.Frame(frm)
    raster_row.grid(row=row, column=0, sticky="w")
    ttk.Radiobutton(raster_row, text="Population density",            variable=raster_var, value="population").grid(row=0, column=0, padx=(0, 12))
    ttk.Radiobutton(raster_row, text="Nighttime lights (2023)",       variable=raster_var, value="nightlights").grid(row=0, column=1, padx=(0, 12))
    ttk.Radiobutton(raster_row, text="GHS — Building volume",         variable=raster_var, value="ghs_volume").grid(row=1, column=0, pady=(4,0))
    ttk.Radiobutton(raster_row, text="GHS — Building surface area",   variable=raster_var, value="ghs_surface").grid(row=1, column=1, pady=(4,0))
    row += 1

    # Year selector (enabled only for datasets that support years)
    year_row = ttk.Frame(frm)
    year_row.grid(row=row, column=0, sticky="w", pady=(6, 0))
    ttk.Label(year_row, text="Year:").grid(row=0, column=0, padx=(0, 8))

    # Default year: keep user's previous or latest available
    def latest_available(key: str) -> int:
        return (years_by_key.get(key) or [2025])[-1]

    year_var = tk.StringVar(value=str(getattr(initial, "raster_year", latest_available(raster_var.get()))))
    year_box = ttk.Combobox(year_row, textvariable=year_var, width=8, state="readonly", values=[str(y) for y in years_by_key["population"]])
    year_box.grid(row=0, column=1)

    # Tiny hint
    hint = ttk.Label(frm, text="Nighttime lights uses 2023 only. \n" 
                     "Global Human Settlement (GHS) layers available every 5 years (1975–2025).", foreground="gray")
    hint.grid(row=row+1, column=0, sticky="w", pady=(4, 0))
    row += 2

    def refresh_year_control(*_):
        key = raster_var.get()
        if key == "nightlights":
            year_box.configure(state="disabled", values=["2023"])
            year_var.set("2023")
        else:
            vals = [str(y) for y in years_by_key.get(key, [])]
            if not vals:
                vals = [str(y) for y in range(1975, 2026, 5)]
            year_box.configure(state="readonly", values=vals)
            # keep current if valid, else pick latest
            if year_var.get() not in vals:
                year_var.set(vals[-1])

    # Wire the radios to update the year combobox
    raster_var.trace_add("write", refresh_year_control)
    refresh_year_control()


    # Buttons
    result = {"opts": None} # default is cancelled unless "OK" is pressed
    def on_ok():
        data = asdict(initial)
        for _, field in schema:
            data[field] = bool_vars[field].get()
        data["raster_choice"] = raster_var.get()
        data["raster_year"]   = int(year_var.get())
        result["opts"] = Options(**data)
        root.destroy()

    def on_cancel():
        result["opts"] = None
        root.destroy()

    btns = ttk.Frame(frm)
    btns.grid(row=row, column=0, sticky="e", pady=(12, 0))
    ttk.Button(btns, text="Cancel", command=on_cancel).grid(row=0, column=0, padx=(0, 8))
    ttk.Button(btns, text="OK", command=on_ok).grid(row=0, column=1)

    # === Right column: image preview (uses pack INSIDE img_frame) ===
    img_frame = ttk.Frame(container)
    img_frame.grid(row=1, column=1, sticky="nsew", padx=(20, 0))
    # Use pack for children within img_frame
    try:
        project_root = os.path.dirname(os.path.dirname(__file__))
        img_path = os.path.join(project_root, "images", "sample.png")
        img = Image.open(img_path)
        img.thumbnail((250, 250))
        img_tk = ImageTk.PhotoImage(img)
        img_label = ttk.Label(img_frame, image=img_tk)
        img_label.image = img_tk
        img_label.pack(expand=True)
        caption = ttk.Label(
            img_frame,
            text="Low-res preview using defaults",
            font=("", 9, "italic"),
            foreground="gray",
            justify="center",
        )
        caption.pack(pady=(6, 0))
    except Exception as e:
        ttk.Label(
            img_frame,
            text=f"No preview available\n({e})",
            font=("", 9, "italic"),
            foreground="gray",
            justify="center",
        ).pack(expand=True)

    # === Let Tk compute best size, then center the window ===
    root.update_idletasks()

    # Make description wrap to actual window width (minus padding)
    def _update_wrap(event=None):
        # total container width minus side padding; clamp to sensible min/max
        wrap = max(400, min(container.winfo_width() - 24, 900))
        desc_label.configure(wraplength=wrap)
    _update_wrap()
    root.bind("<Configure>", _update_wrap)

    # Center without forcing a fixed size
    w = root.winfo_reqwidth()
    h = root.winfo_reqheight()
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = max(0, (sw - w) // 2)
    y = max(0, (sh - h) // 2)
    root.geometry(f"+{x}+{y}")

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
