"""Flooded buildings by municipality and valley, and the comparison with the published paper."""
import pandas as pd

# Detoni, Faccin, Silveira, Rorato & Machado (2025), RBGDR 21(1): Quadros 1 and 2,
# % of buildings flooded in (rural, urban) areas
PUBLISHED_PCT = {
    "Sinimbu": (2.79, 18.51), "Venâncio Aires": (10.66, 16.89), "Rio Pardo": (6.87, 9.2),
    "Candelária": (5.86, 8.71), "Santa Cruz do Sul": (1.49, 5.36), "Vera Cruz": (7.7, 3.25),
    "Vale do Sol": (1.12, 0), "Passo do Sobrado": (4.09, 0),
    "Marques de Souza": (12.92, 53.63), "Muçum": (16.76, 50.66), "Roca Sales": (8.96, 43.91),
    "Cruzeiro do Sul": (29.11, 43.44), "Estrela": (11.03, 40.24), "Travesseiro": (10.32, 29.66),
    "Encantado": (12.33, 25.81), "Colinas": (12.18, 23.78), "Arroio do Meio": (7.32, 20.07),
    "Forquetinha": (16.3, 14.07), "Lajeado": (0, 8.25), "Relvado": (1.27, 0), "Imigrante": (0.88, 0),
    "Doutor Ricardo": (1.44, 0), "Canudos do Vale": (2.58, 0),
}
PUBLISHED_VALLEY = {"Vale do Rio Pardo": 16967, "Vale do Taquari": 26624}
PUBLISHED_CITY = {"Arroio do Meio": 2635, "Cruzeiro do Sul": 3942, "Estrela": 6500, "Lajeado": 3122}


def by_municipality(b, mun):
    g = b.groupby(["cd_mun", "urban"]).agg(buildings=("flooded", "size"), flooded=("flooded", "sum")).unstack(fill_value=0)
    t = pd.DataFrame({
        "buildings": g["buildings"].sum(axis=1), "flooded": g["flooded"].sum(axis=1),
        "buildings_urban": g["buildings"].get(True, 0), "flooded_urban": g["flooded"].get(True, 0),
        "buildings_rural": g["buildings"].get(False, 0), "flooded_rural": g["flooded"].get(False, 0),
    })
    t["flooded_centroid"] = b.groupby("cd_mun")["flooded_centroid"].sum()
    t = mun.drop(columns="geometry").merge(t, left_on="cd_mun", right_index=True, how="inner")
    for k in ("", "_urban", "_rural"):
        t[f"pct{k}"] = (100 * t[f"flooded{k}"] / t[f"buildings{k}"]).where(t[f"buildings{k}"] > 0, 0)
    return t.sort_values("flooded", ascending=False).reset_index(drop=True)


def by_valley(t):
    v = t.groupby("valley")[["buildings", "flooded", "buildings_urban", "flooded_urban", "buildings_rural",
                             "flooded_rural", "flooded_centroid"]].sum()
    v.loc["Both valleys"] = v.sum()
    v["pct"] = 100 * v["flooded"] / v["buildings"]
    v["pct_urban"] = 100 * v["flooded_urban"] / v["buildings_urban"]
    return v.reset_index()


def compare(t, v):
    """Computed vs published values: counts within 1%, shares within 0.5 percentage points."""
    rows = []
    vt = v.set_index("valley")
    for valley, n in PUBLISHED_VALLEY.items():
        rows.append({"item": f"{valley}: flooded buildings", "published": n, "computed": int(vt.loc[valley, "flooded"])})
    tt = t.set_index("municipality")
    for city, n in PUBLISHED_CITY.items():
        rows.append({"item": f"{city}: flooded buildings", "published": n, "computed": int(tt.loc[city, "flooded"])})
    for city, (rural, urban) in PUBLISHED_PCT.items():
        if city in tt.index:
            rows.append({"item": f"{city}: % urban buildings flooded", "published": urban,
                         "computed": round(float(tt.loc[city, "pct_urban"]), 2)})
            rows.append({"item": f"{city}: % rural buildings flooded", "published": rural,
                         "computed": round(float(tt.loc[city, "pct_rural"]), 2)})
    out = pd.DataFrame(rows)
    out["difference"] = (out["computed"] - out["published"]).round(2)
    is_pct = out["item"].str.contains("%")
    out["ok"] = (is_pct & (out["difference"].abs() <= 0.5)) | (~is_pct & (out["difference"].abs() <= 0.01 * out["published"]))
    return out
