"""Run the cleaning pipeline and write the cleaned CSV + cleaning log (D4)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import config  # noqa: E402
from src.data_loading import load_clean  # noqa: E402

df, rep = load_clean(config.RAW_CSV)
config.CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)
df.to_csv(config.CLEAN_CSV, index=False)
config.CLEANING_LOG.parent.mkdir(parents=True, exist_ok=True)
config.CLEANING_LOG.write_text(rep.to_markdown(), encoding="utf-8")
print(f"raw={rep.raw_rows} clean={rep.clean_rows} -> {config.CLEAN_CSV}")
