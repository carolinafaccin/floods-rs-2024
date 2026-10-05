"""FLOODS-RS-2024 pipeline: flood extent of 6 May 2024 + Open Buildings -> tables and figures.

    python pipeline.py                       # everything
    python pipeline.py --only tables         # tables and comparison with the paper
    python pipeline.py --only figures docs   # redraw figures and copy the README ones

Inputs come from sources_dir and outputs go to outputs_dir, both set in config/config.local.json.
"""
import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from floods import config, data, figures, metrics, style  # noqa: E402

README_FIGURES = ["map_region", "flooded_by_municipality", "share_flooded"] + [f"map_{t[0]}" for t in figures.TOWNS]


def run_tables(t, outputs_dir):
    out = outputs_dir / "tables"
    t.round(2).to_csv(out / "flooded_by_municipality.csv", index=False)
    v = metrics.by_valley(t)
    v.round(2).to_csv(out / "flooded_by_valley.csv", index=False)
    cmp = metrics.compare(t, v)
    cmp.to_csv(out / "comparison_with_paper.csv", index=False)
    for _, r in v.iterrows():
        print(f"  {r['valley']}: {int(r['flooded']):,} of {int(r['buildings']):,} buildings flooded "
              f"({r['pct']:.1f}%; {r['pct_urban']:.1f}% of urban buildings)")
    for _, r in cmp.head(6).iterrows():
        print(f"  {'ok ' if r['ok'] else 'FAIL'} {r['item']}: published {r['published']:,.0f}, computed {r['computed']:,.0f}")
    print(f"  shares by municipality: {int(cmp['ok'].sum()) - 6} of {len(cmp) - 6} within 0.5 points of the paper")
    return cmp["ok"].all()


def run_figures(b, t, mun, pdir, outputs_dir):
    style.setup()
    f = outputs_dir / "figures"
    flood = data.load_flood(pdir)
    rivers = data.load_rivers(pdir)
    roads = data.load_roads(pdir)
    vb = b[b["cd_mun"].isin(mun["cd_mun"])]
    figures.map_region(vb, mun, flood, rivers, f / "map_region.png")
    figures.flooded_by_municipality(t, f / "flooded_by_municipality.png")
    figures.share_flooded(t, f / "share_flooded.png")
    for spec in figures.TOWNS:
        x0, y0, x1, y1 = figures._box(*spec[2:6])
        water = data.load_water(pdir, (x0, y0, x1, y1))
        figures.map_town(spec, b, t, flood, water, rivers, roads, mun, f / f"map_{spec[0]}.png")
    print(f"figures written to {f}")


def run_docs(outputs_dir):
    dest = Path(__file__).parent / "docs" / "img"
    dest.mkdir(parents=True, exist_ok=True)
    for name in README_FIGURES:
        shutil.copy(outputs_dir / "figures" / f"{name}.png", dest / f"{name}.png")
    print(f"copied {len(README_FIGURES)} figures to {dest}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--only", nargs="+", choices=["tables", "figures", "docs"])
    args = p.parse_args()
    steps = args.only or ["tables", "figures", "docs"]

    sources_dir, outputs_dir = config.load()
    pdir = config.project_dir(sources_dir)
    flood = data.load_flood(pdir)
    mun = data.load_municipalities(pdir, sources_dir)
    b = data.load_buildings(sources_dir, pdir, flood, outputs_dir / "cache" / "buildings.parquet")
    t = metrics.by_municipality(b, mun)
    print(f"{len(b):,} buildings, {int(b['flooded'].sum()):,} inside the flood extent; {len(mun)} municipalities in the two valleys")
    ok = True
    if "tables" in steps:
        ok = run_tables(t, outputs_dir)
    if "figures" in steps:
        run_figures(b, t, mun, pdir, outputs_dir)
    if "docs" in steps:
        run_docs(outputs_dir)
    if not ok:
        sys.exit("validation failed: computed values differ from the published ones (see tables/comparison_with_paper.csv)")


if __name__ == "__main__":
    main()
