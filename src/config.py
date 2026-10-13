"""Central configuration: paths, reference data, default thresholds."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data" / "raw" / "nassau_candy_raw.csv"
CLEAN_CSV = ROOT / "data" / "processed" / "nassau_candy_clean.csv"
CLEANING_LOG = ROOT / "docs" / "cleaning_log.md"

APP_TITLE = "Nassau Candy Product Line Profitability & Margin Performance Analysis"

# Default thresholds (all user-adjustable in the app where noted)
DEFAULT_MARGIN_THRESHOLD = 0.50     # Reprice if product gross margin % < this (slider)
COST_RATIO_THRESHOLD = 0.60         # Cost renegotiation if Cost/Sales >= this
HEALTHY_VOLUME_QUANTILE = 0.50      # "Healthy volume" = units >= this quantile of products
LOW_SALES_QUANTILE = 0.25           # "Low sales" = product sales <= this quantile
PRICING_COST_TOL = 0.15             # Pricing inefficiency: unit cost within +/-15%
PRICING_MARGIN_GAP = 0.20           # ...but gross margin differs by >= 20 pp
PRODUCT_SEARCH_CUTOFF = 60          # rapidfuzz score cutoff (0-100)

# Reference data (PRD 7.2). Coordinates are APPROXIMATE metro-level points;
# replace with exact plant addresses in this file when available.
FACTORIES = {
    "Lot's O' Nuts":     {"state": "AZ", "lat": 33.3062, "lon": -111.8413, "divisions": ["Chocolate"]},
    "Wicked Choccy's":   {"state": "GA", "lat": 33.7490, "lon": -84.3880,  "divisions": ["Chocolate"]},
    "Sugar Shack":       {"state": "MN", "lat": 44.9778, "lon": -93.2650,  "divisions": ["Sugar", "Other"]},
    "Secret Factory":    {"state": "IL", "lat": 41.8781, "lon": -87.6298,  "divisions": ["Sugar", "Other"]},
    "The Other Factory": {"state": "TN", "lat": 36.1627, "lon": -86.7816,  "divisions": ["Sugar", "Other"]},
}

# Canonical product-name corrections beyond whitespace normalisation (DQ-4)
PRODUCT_NAME_OVERRIDES: dict[str, str] = {}
