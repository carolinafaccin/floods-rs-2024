"""Figures in the project's visual identity (brand palette, Source Code Pro)."""
import textwrap

import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import shapely
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

from . import style
from .config import CRS

URBAN, RURAL = style.CAT[1], style.CAT[0]   # rust, green (validated adjacent pair)
FLOOD = style.PEACH                          # flood extent of 6 May 2024
FLOODED = style.ORANGE                       # flooded buildings
DRY = "#B9B1A8"                              # other buildings
RIVER = "#A9BCA0"
HEAD, FOOT = 1.5, 0.6

# Town maps: (slug, title, lat, lon, width km, height km, municipalities summarized)
TOWNS = [
    ("lajeado_estrela", "Lajeado, Estrela, Arroio do Meio and Cruzeiro do Sul", -29.455, -51.962, 15, 17,
     ["Estrela", "Cruzeiro do Sul", "Lajeado", "Arroio do Meio"]),
    ("encantado_mucum", "Encantado, Roca Sales and Muçum", -29.232, -51.872, 10, 17.5, ["Encantado", "Roca Sales", "Muçum"]),
    ("santa_cruz", "Santa Cruz do Sul and Vera Cruz", -29.718, -52.462, 16, 11, ["Santa Cruz do Sul", "Vera Cruz"]),
    ("rio_pardo", "Rio Pardo", -29.985, -52.375, 9, 8, ["Rio Pardo"]),
    ("candelaria", "Candelária", -29.668, -52.79, 8, 7, ["Candelária"]),
    ("marques_de_souza", "Marques de Souza and Travesseiro", -29.318, -52.08, 9, 8, ["Marques de Souza", "Travesseiro"]),
    ("sinimbu", "Sinimbu", -29.537, -52.528, 5, 4.5, ["Sinimbu"]),
]


def _box(lat, lon, w_km, h_km):
    c = gpd.GeoSeries([shapely.Point(lon, lat)], crs=4674).to_crs(CRS).iloc[0]
    return (c.x - w_km * 500, c.y - h_km * 500, c.x + w_km * 500, c.y + h_km * 500)


def _legend(fig, handles, x, y, title=None, **kw):
    opts = dict(loc="upper left", bbox_to_anchor=(x, y), fontsize=8.5, title_fontsize=9, handlelength=1.2,
                alignment="left", labelspacing=0.7)
    opts.update(kw)
    leg = fig.legend(handles=handles, title=title, **opts)
    leg.get_title().set_fontweight("semibold")
    return leg


def _fmt(n):
    return f"{int(n):,}"


def flooded_by_municipality(t, out, min_flooded=50):
    """Flooded buildings per municipality, urban and rural, one panel per valley."""
    d = t[t["flooded"] >= min_flooded]
    valleys = ["Vale do Taquari", "Vale do Rio Pardo"]
    sizes = [int((d["valley"] == v).sum()) for v in valleys]
    W, H = 11, 2.6 + 0.3 * sum(sizes)
    fig, axes = plt.subplots(2, 1, figsize=(W, H), sharex=True, gridspec_kw={"height_ratios": sizes})
    fig.subplots_adjust(left=0.2, right=0.93, top=1 - (HEAD + 0.45) / H, bottom=(FOOT + 0.45) / H, hspace=0.25)
    xmax = d["flooded"].max() * 1.12
    for ax, valley in zip(axes, valleys):
        s = d[d["valley"] == valley].sort_values("flooded")
        y = np.arange(len(s))
        ax.barh(y, s["flooded_urban"], color=URBAN, height=0.62, edgecolor="white", linewidth=1)
        ax.barh(y, s["flooded_rural"], left=s["flooded_urban"], color=RURAL, height=0.62, edgecolor="white", linewidth=1)
        for i, n in enumerate(s["flooded"]):
            ax.text(n + xmax * 0.008, i, _fmt(n), va="center", fontsize=8, color=style.INK)
        ax.set_yticks(y)
        ax.set_yticklabels(s["municipality"], fontsize=8.5)
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        ax.grid(axis="y", visible=False)
        ax.set_xlim(0, xmax)
        total = t.loc[t["valley"] == valley, "flooded"].sum()
        ax.set_title(f"{valley}: {_fmt(total)} flooded buildings", loc="left", fontsize=10, fontweight="semibold",
                     color=style.INK)
    axes[-1].set_xlabel("Flooded buildings")
    axes[-1].xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: _fmt(v)))
    _legend(fig, [Patch(facecolor=URBAN, label="Urban census tracts"), Patch(facecolor=RURAL, label="Rural census tracts")],
            0.035, 1 - (HEAD - 0.05) / H, ncol=2, columnspacing=1.6)
    style.header(fig, "Buildings reached by the May 2024 flood",
                 f"Open Buildings footprints inside the flood extent of 6 May 2024, by municipality "
                 f"(at least {min_flooded} flooded buildings).")
    style.footer(fig)
    style.save(fig, out)


def share_flooded(t, out, min_flooded=50):
    """Share of buildings flooded, urban vs rural tracts (the paper's Quadros 1 and 2)."""
    d = t[t["flooded"] >= min_flooded].sort_values("pct_urban")
    W, H = 11, 2.4 + 0.3 * len(d)
    fig, ax = plt.subplots(figsize=(W, H))
    fig.subplots_adjust(left=0.27, right=0.95, top=1 - (HEAD + 0.4) / H, bottom=(FOOT + 0.45) / H)
    y = np.arange(len(d))
    for i, (_, r) in enumerate(d.iterrows()):
        ax.plot([r["pct_rural"], r["pct_urban"]], [i, i], color=style.GREY, lw=2, zorder=1)
    ax.scatter(d["pct_rural"], y, s=55, color=RURAL, edgecolor="white", linewidth=1.5, zorder=3)
    ax.scatter(d["pct_urban"], y, s=55, color=URBAN, edgecolor="white", linewidth=1.5, zorder=3)
    for i, v in enumerate(d["pct_urban"]):
        if v >= 25:
            ax.text(v + 1.4, i, f"{v:.0f}%", va="center", fontsize=8, color=style.INK)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{m}  ·  {'Taquari' if v == 'Vale do Taquari' else 'Rio Pardo'}"
                        for m, v in zip(d["municipality"], d["valley"])], fontsize=8.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(60, d["pct_urban"].max() + 8))
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}%"))
    ax.set_xlabel("Share of buildings flooded")
    _legend(fig, [Line2D([], [], marker="o", ls="", color=URBAN, markersize=7, label="Urban census tracts"),
                  Line2D([], [], marker="o", ls="", color=RURAL, markersize=7, label="Rural census tracts")],
            0.035, 1 - (HEAD - 0.05) / H, ncol=2, columnspacing=1.6)
    style.header(fig, "In the small Taquari towns, half the urban buildings flooded",
                 "Share of buildings inside the flood extent, in urban and rural census tracts (2010), by municipality.")
    style.footer(fig)
    style.save(fig, out)


def map_region(b, mun, flood, rivers, out):
    """Overview: the two valleys, the flood extent and where the town maps are."""
    W, H = 10, 11.5
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.01, FOOT / H, 0.7, 1 - (HEAD + FOOT) / H])
    region = mun.union_all()
    for valley, color in zip(["Vale do Rio Pardo", "Vale do Taquari"], [style.LAND, "#ECE6DE"]):
        mun[mun["valley"] == valley].plot(ax=ax, color=color, edgecolor="white", linewidth=0.6, zorder=0)
    gpd.GeoSeries([region], crs=CRS).boundary.plot(ax=ax, color=style.INK, linewidth=0.8, zorder=4)
    flood.clip(region).plot(ax=ax, color=FLOOD, linewidth=0, zorder=1)
    rivers.clip(region).plot(ax=ax, color=RIVER, linewidth=0.8, zorder=2)
    f = b[b["flooded"]]
    ax.scatter(f["x"], f["y"], s=0.4, color=FLOODED, linewidth=0, zorder=3)
    for i, (slug, title, lat, lon, w, h, _) in enumerate(TOWNS, 1):
        x0, y0, x1, y1 = _box(lat, lon, w, h)
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor=style.INK, linewidth=0.9, zorder=5))
        ax.text(x1 + 800, y1, str(i), fontsize=9, fontweight="semibold", color=style.INK, va="top",
                path_effects=style.halo(), zorder=6)
    minx, miny, maxx, maxy = mun.total_bounds
    style.map_axes(ax, (minx, miny, maxx, maxy), pad=2000)
    style.scalebar(ax, km=20)
    x0 = 0.73
    _legend(fig, [Patch(facecolor=FLOOD, label="Flood extent, 6 May 2024"),
                  Line2D([], [], marker="o", ls="", color=FLOODED, markersize=4, label="Flooded buildings"),
                  Line2D([], [], color=RIVER, lw=1.5, label="Main rivers"),
                  Patch(facecolor="#ECE6DE", label="Vale do Taquari"),
                  Patch(facecolor=style.LAND, label="Vale do Rio Pardo")], x0, 1 - HEAD / H)
    _legend(fig, [Line2D([], [], ls="", label=textwrap.fill(f"{i}  {t[1].replace(' and ', ', ')}", 30, subsequent_indent="   ")) for i, t in enumerate(TOWNS, 1)], x0, 1 - HEAD / H - 0.2,
            "Town maps", handlelength=0, handletextpad=0, fontsize=8)
    style.header(fig, "The May 2024 flood in the Rio Pardo and Taquari valleys",
                 f"{_fmt(f.shape[0])} buildings inside the flood extent in the two valleys "
                 f"({len(mun)} municipalities).")
    style.footer(fig)
    style.save(fig, out)


def map_town(spec, b, t, flood, water, rivers, roads, mun, out):
    """Town map: flood extent, buildings and flooded buildings."""
    slug, title, lat, lon, w, h, names = spec
    x0, y0, x1, y1 = _box(lat, lon, w, h)
    aspect = w / h
    W = 11
    map_h = (W * 0.72) / aspect
    H = map_h + HEAD + FOOT + 0.2
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([0.01, FOOT / H, 0.72, map_h / H])
    view = shapely.box(x0, y0, x1, y1)
    flood.clip(view).plot(ax=ax, color=FLOOD, linewidth=0, zorder=1)
    if water is not None:
        water.clip(view).plot(ax=ax, color=style.WATER, linewidth=0, zorder=2)
    rivers.clip(view).plot(ax=ax, color=RIVER, linewidth=1.2, zorder=2)
    mun.boundary.clip(view).plot(ax=ax, color=style.MUTED, linewidth=0.6, linestyle=(0, (4, 3)), zorder=3)
    inside = b[(b["x"] > x0) & (b["x"] < x1) & (b["y"] > y0) & (b["y"] < y1)]
    inside[~inside["flooded"]].plot(ax=ax, color=DRY, linewidth=0, zorder=4)
    inside[inside["flooded"]].plot(ax=ax, color=FLOODED, linewidth=0, zorder=5)
    r = roads.clip(view)
    r.plot(ax=ax, color=style.INK, linewidth=1.1, zorder=6)
    for name, g in r.dissolve("RODOVIA").iterrows():
        if g.geometry.length > 1500:
            p = g.geometry.interpolate(0.5, normalized=True)
            ax.text(p.x, p.y, name, fontsize=7.5, fontweight="semibold", color=style.INK, ha="center", va="center",
                    path_effects=style.halo(2.5), zorder=7)
    for _, m in mun[mun["municipality"].isin(names)].iterrows():
        sub = inside[(inside["cd_mun"] == m["cd_mun"])]
        if len(sub):
            cx, cy = sub["x"].median(), sub["y"].median()
            ax.text(cx, cy, m["municipality"], fontsize=10, fontweight="semibold", color=style.INK, ha="center",
                    va="center", path_effects=style.halo(3), zorder=8)
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_color(style.GREY)
    style.scalebar(ax, km=1 if w <= 9 else 2, loc=(0.04, 0.04))
    lx, ly = 0.75, 1 - HEAD / H
    _legend(fig, [Patch(facecolor=FLOOD, label="Flood extent,\n6 May 2024"), Patch(facecolor=FLOODED, label="Flooded buildings"),
                  Patch(facecolor=DRY, label="Other buildings"), Patch(facecolor=style.WATER, label="Rivers"),
                  Line2D([], [], color=style.INK, lw=1.2, label="State highways"),
                  Line2D([], [], color=style.MUTED, lw=0.8, ls=(0, (4, 3)), label="Municipal limits")], lx, ly)
    rows = t.set_index("municipality").loc[[n for n in names if n in set(t["municipality"])]]
    stats = [Line2D([], [], ls="", label=f"{m}\n{_fmt(r['flooded'])} buildings · {r['pct_urban']:.0f}% urban")
             for m, r in rows.iterrows()]
    _legend(fig, stats, lx, ly - 2.45 / H, "Flooded buildings", handlelength=0, handletextpad=0, fontsize=8,
            labelspacing=0.9)
    style.header(fig, title, "Flood extent of 6 May 2024 and the buildings it reached. The figures on the right count\n"
                             "flooded buildings in the whole municipality and the share of its urban buildings flooded.")
    style.footer(fig)
    style.save(fig, out)
