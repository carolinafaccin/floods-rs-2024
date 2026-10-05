"""The pipeline must reproduce the numbers published in the paper (needs sources_dir; skipped without it)."""
import pytest

from floods import config, data, metrics

CFG = config.ROOT / "config" / "config.local.json"
pytestmark = pytest.mark.skipif(not CFG.exists(), reason="config/config.local.json not set")


def test_published_numbers():
    sources_dir, outputs_dir = config.load()
    pdir = config.project_dir(sources_dir)
    flood = data.load_flood(pdir)
    mun = data.load_municipalities(pdir, sources_dir)
    b = data.load_buildings(sources_dir, pdir, flood, outputs_dir / "cache" / "buildings.parquet")
    t = metrics.by_municipality(b, mun)
    cmp = metrics.compare(t, metrics.by_valley(t))
    assert cmp["ok"].all(), cmp[~cmp["ok"]].to_string()
