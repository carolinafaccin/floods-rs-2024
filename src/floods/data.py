"""Load the flood extent, the buildings and the context layers."""
import geopandas as gpd
import pandas as pd
import shapely

from .config import BUILDINGS, COREDES, CRS, FLOOD, MUNICIPALITIES, RIVERS, ROADS, TRACTS, VALLEYS, WATER


def load_flood(pdir):
    """Flood extent observed on 6 May 2024 (one polygon for the Guaíba hydrographic region)."""
    f = gpd.read_file(pdir / FLOOD).to_crs(CRS)
    f["geometry"] = f.geometry.force_2d().make_valid()
    return f[["geometry"]]


def load_municipalities(pdir, raw_dir):
    """Municipalities of the Rio Pardo and Taquari valleys (COREDE regions), with their valley."""
    m = gpd.read_file(pdir / MUNICIPALITIES).to_crs(CRS)
    m = m.rename(columns={"CD_MUN": "cd_mun", "NM_MUN": "municipality"})
    coredes = pd.read_excel(raw_dir / COREDES, dtype={"geocod": str})
    m = m.merge(coredes[["geocod", "corede"]], left_on="cd_mun", right_on="geocod", how="left")
    m = m[m["corede"].isin(VALLEYS)].rename(columns={"corede": "valley"})
    return m[["cd_mun", "municipality", "valley", "geometry"]].reset_index(drop=True)


def load_buildings(raw_dir, pdir, flood, cache):
    """Open Buildings footprints with municipality, census tract (2010), urban/rural and a `flooded` flag.

    A building counts as flooded when its footprint touches the flood extent, as in the 2024 analysis
    (`flooded_centroid` keeps the stricter test: centroid inside the extent). It takes the
    urban/rural situation of the 2010 census tract that contains its centroid. The source shapefile
    is large, so the result is cached as GeoParquet in data_dir/cache.
    """
    if cache.exists():
        return gpd.read_parquet(cache)
    b = gpd.read_file(raw_dir / BUILDINGS, columns=["area_in_me", "confidence"]).to_crs(CRS)
    b = b.rename(columns={"area_in_me": "area_m2"})
    c = b.geometry.centroid
    b["x"], b["y"] = c.x, c.y
    area = flood.union_all()
    shapely.prepare(area)
    b["flooded"] = shapely.intersects(area, b.geometry.values)
    b["flooded_centroid"] = shapely.contains_xy(area, b["x"].values, b["y"].values)
    tracts = gpd.read_file(pdir / TRACTS, columns=["CD_GEOCODI", "TIPO", "CD_GEOCODM"]).to_crs(CRS)
    pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(b["x"], b["y"]), crs=CRS, index=b.index)
    j = gpd.sjoin(pts, tracts, how="left", predicate="within")
    j = j[~j.index.duplicated()]
    b["tract_2010"] = j["CD_GEOCODI"]
    b["cd_mun"] = j["CD_GEOCODM"]
    b["urban"] = j["TIPO"].eq("URBANO")
    b.to_parquet(cache)
    return b


def load_rivers(pdir):
    r = gpd.read_file(pdir / RIVERS).to_crs(CRS)
    return r[["nome", "geometry"]]


def load_water(pdir, bounds):
    """IBGE water bodies (rivers wider than a line) inside bounds; the file is already in SIRGAS 2000 / UTM 22S."""
    return gpd.read_file(pdir / WATER, bbox=tuple(bounds)).to_crs(CRS)[["geometry"]]


def load_roads(pdir):
    r = gpd.read_file(pdir / ROADS).to_crs(CRS)
    return r[["RODOVIA", "geometry"]]
