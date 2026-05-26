"""Browse the 53-incident empirical catalog."""
from __future__ import annotations
import csv
from pathlib import Path
import sys


def load_catalog() -> list[dict]:
    """Load the catalog CSV. Looks in standard locations."""
    # Try a few known locations
    candidates = [
        Path(__file__).resolve().parent / "resources" / "catalog.csv",
        Path(__file__).resolve().parent.parent.parent / "paper" / "supplement" / "catalog.csv",
    ]
    path = None
    for c in candidates:
        if c.exists():
            path = c
            break
    if path is None:
        return []
    entries = []
    with open(path) as f:
        for row in csv.DictReader(f):
            row["loss_usd"] = float(row["loss_usd"])
            entries.append(row)
    return entries
