"""Paths: read from config/config.local.json (gitignored), like the other repositories.

- raw_dir   shared raw-data catalog (read only)
- data_dir  this project's outputs (tables, figures, cache/)
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CRS = 31982  # SIRGAS 2000 / UTM 22S

# GIS project of the 2024 analysis (moved once during the raw_dir reorganization)
PROJECT_DIRS = ("_projetos/rio_pardo_enchentes_2024/shp", "_archive/projetos/rio_pardo_enchentes_2024/shp")
FLOOD = "rhguaiba_inundacao_obs_06-05-24.shp"                       # Possantti et al. (2024), 6 May 2024
TRACTS = "rs_ibge_setor_censitario_2010.shp"                         # IBGE census tracts 2010 (urban / rural)
MUNICIPALITIES = "RS_Municipios_2022.shp"
RIVERS = "rs_hid_trecho_drenagem_l_ibge_rio_destaque.shp"
WATER = "rs_hid_trecho_massa_dagua_a_ibge.shp"
ROADS = "rs_daer_rodovias_2014_recortado_rgi_scs-lajeado.shp"
COREDES = "spgg_rs/coredes/t1/coredes_munic_geocod.xlsx"
BUILDINGS = "google/open_buildings/vales_rs_2024/t1/v_openbuildings_vales_2024.shp"  # Open Buildings v3, confidence >= 0.075
VALLEYS = ["Vale do Rio Pardo", "Vale do Taquari"]


def load():
    """Return (raw_dir, data_dir) as Paths; create data_dir subfolders."""
    cfg_path = ROOT / "config" / "config.local.json"
    if not cfg_path.exists():
        raise SystemExit(f"Missing {cfg_path.name}: copy config/config.local.json.example and set raw_dir and data_dir.")
    cfg = json.loads(cfg_path.read_text())
    raw_dir, data_dir = Path(cfg["raw_dir"]), Path(cfg["data_dir"])
    if not raw_dir.exists():
        raise SystemExit(f"raw_dir not found: {raw_dir}")
    for sub in ("tables", "figures", "cache"):
        (data_dir / sub).mkdir(parents=True, exist_ok=True)
    return raw_dir, data_dir


def project_dir(raw_dir):
    for rel in PROJECT_DIRS:
        p = raw_dir / rel
        if (p / FLOOD).exists():
            return p
    raise SystemExit("flood project folder not found under raw_dir (" + " or ".join(PROJECT_DIRS) + ")")
