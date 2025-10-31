#!/usr/bin/env python3
import argparse
import os
import re
import numpy as np
import rasterio
import geopandas as gpd
from shapely.geometry import Point

COUNTRY_COL_PREF = ("name", "NAME", "ADMIN", "Country", "country", "NAME_EN")

def parse_year_from_filename(path: str, fallback: str = "value") -> str:
    """
    Returns a column name consistent with your timeseries style.
    Prefers a 4-digit year (e.g., 2024) in the filename; otherwise uses fallback.
    """
    fname = os.path.basename(path)
    # Try EYYYY (like your GHS files), or any 4-digit year
    m = re.search(r"E(\d{4})", fname)
    if m:
        return m.group(1)
    m = re.search(r"(\d{4})", fname)
    return m.group(1) if m else fallback

def create_reference_grid(src):
    rows, cols = np.indices((src.height, src.width))
    xs, ys = rasterio.transform.xy(src.transform, rows.ravel(), cols.ravel(), offset="center")
    point_indices = (rows.ravel() * src.width + cols.ravel()).astype(int)
    gdf = gpd.GeoDataFrame(
        {"point_index": point_indices},
        geometry=[Point(x, y) for x, y in zip(xs, ys)],
        crs=src.crs,
    )
    return gdf

def add_raster_column(gdf, raster_path, col_name):
    with rasterio.open(raster_path) as src:
        data = src.read(1).ravel()
        data = np.round(data, 2).astype("float32") # previously too large with 64-bit precision float
    gdf[col_name] = data
    return gdf

def spatial_join_countries(gdf, countries_path):
    countries = gpd.read_file(countries_path)

    # keep only the desired country name column + geometry
    for cand in ("name", "NAME", "ADMIN", "Country", "country", "NAME_EN"):
        if cand in countries.columns:
            countries = countries[[cand, "geometry"]].rename(columns={cand: "country"})
            break
    else:
        # fallback if none of the expected columns are present
        countries["country"] = None
        countries = countries[["country", "geometry"]]

    if countries.crs != gdf.crs:
        countries = countries.to_crs(gdf.crs)

    out = gpd.sjoin(gdf, countries, how="left", predicate="within")
    if "index_right" in out.columns:
        out = out.drop(columns=["index_right"])
    return out


def main():
    ap = argparse.ArgumentParser(description="Convert a single raster to a 'timeseries-style' points GeoPackage (matching your existing schema).")
    ap.add_argument("--raster", default="data/rasters/nightlight_2024.tif", help="Path to input .tif")
    ap.add_argument("--out", default="data/rasters/nightlight_timeseries_points.gpkg", help="Output GPKG path")
    ap.add_argument("--layer", default="points", help="Output layer name (default: points)")
    ap.add_argument("--countries", default="data/countries_simplified.gpkg", help="Optional countries GPKG for join (default mirrors your script). Use '' to skip.")
    ap.add_argument("--col-name", default=None, help="Override the data column name (e.g., 2024). Defaults to a year parsed from the filename.")
    args = ap.parse_args()

    # Open raster and build reference grid (exactly like your pipeline)
    with rasterio.open(args.raster) as src:
        gdf = create_reference_grid(src)
        data_col = args.col_name or parse_year_from_filename(args.raster, fallback="value")
        gdf = add_raster_column(gdf, args.raster, data_col)

    # Spatial join with countries (optional, same 'within' predicate)
    if args.countries and args.countries.strip():
        try:
            gdf = spatial_join_countries(gdf, args.countries)
        except Exception as e:
            print(f"  Warning: countries join failed: {e}")

    # Reorder columns to match your GPKG tables
    cols_order = ["point_index"]
    if "country" in gdf.columns:
        cols_order.append("country")
    cols_order += [data_col, "geometry"]
    # keep extras (if any) at the end but preserve the main order
    gdf = gdf[[c for c in cols_order if c in gdf.columns] + [c for c in gdf.columns if c not in cols_order]]

    # Write GPKG (layer 'points' by default)
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    gdf.to_file(args.out, driver="GPKG", layer=args.layer)

    size_mb = os.path.getsize(args.out) / (1024 * 1024)
    print(f"→ Created: {args.out} ({size_mb:.2f} MB)")
    print(f"   Features: {len(gdf):,}")
    print(f"   Columns: {list(gdf.columns)}")

if __name__ == "__main__":
    main()
