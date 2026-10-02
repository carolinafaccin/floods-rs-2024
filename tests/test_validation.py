"""The pipeline must reproduce the numbers published in the paper (needs raw_dir; skipped without it)."""
import pytest

from floods import config, data, metrics

CFG = config.ROOT / "config" / "config.local.json"
pytestmark = pytest.mark.skipif(not CFG.exists(), reason="config/config.local.json not set")


def test_published_numbers():
    raw_dir, data_dir = config.load()
    pdir = config.project_dir(raw_dir)
    flood = data.load_flood(pdir)
    mun = data.load_municipalities(pdir, raw_dir)
    b = data.load_buildings(raw_dir, pdir, flood, data_dir / "cache" / "buildings.parquet")
    t = metrics.by_municipality(b, mun)
    cmp = metrics.compare(t, metrics.by_valley(t))
    assert cmp["ok"].all(), cmp[~cmp["ok"]].to_string()
