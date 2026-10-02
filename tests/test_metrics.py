"""Unit tests on synthetic data."""
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

from floods import metrics


def _data():
    mun = gpd.GeoDataFrame({"cd_mun": ["1", "2"], "municipality": ["A", "B"], "valley": ["Vale do Taquari", "Vale do Rio Pardo"]},
                           geometry=[box(0, 0, 1, 1), box(1, 0, 2, 1)], crs=31982)
    b = pd.DataFrame({
        "cd_mun": ["1", "1", "1", "1", "2", "2", "3"],
        "urban": [True, True, False, False, True, False, True],
        "flooded": [True, False, True, False, False, False, True],
        "flooded_centroid": [True, False, False, False, False, False, True],
    })
    return b, mun


def test_by_municipality_shares():
    b, mun = _data()
    t = metrics.by_municipality(b, mun).set_index("municipality")
    assert t.loc["A", "flooded"] == 2 and t.loc["A", "pct_urban"] == 50 and t.loc["A", "pct_rural"] == 50
    assert t.loc["B", "flooded"] == 0
    assert "3" not in set(t["cd_mun"])  # buildings outside the two valleys are left out


def test_by_valley_totals():
    b, mun = _data()
    v = metrics.by_valley(metrics.by_municipality(b, mun)).set_index("valley")
    assert v.loc["Both valleys", "buildings"] == 6 and v.loc["Both valleys", "flooded"] == 2
    assert v.loc["Both valleys", "flooded_centroid"] == 1
