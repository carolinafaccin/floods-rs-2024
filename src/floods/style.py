"""Figure style: the brand (brand.py, synced from the lina-brand repository) plus this
repository's source line. Colors, palettes and helpers come from brand.py; edit them there."""
from . import brand
from .brand import *  # noqa: F401,F403  colors, data palettes, header, scalebar, halo, save...
from .config import ROOT

SOURCE = "Source: Possantti et al. (2024) flood extent; Google Open Buildings v3; IBGE; DAER-RS. Own calculations."
REPO = "github.com/carolinafaccin/floods-rs-2024"


def setup():
    """Register the bundled fonts (OFL) and set the matplotlib defaults."""
    brand.setup(ROOT / "assets" / "fonts")


def footer(fig, note=SOURCE):
    brand.footer(fig, note, REPO)
