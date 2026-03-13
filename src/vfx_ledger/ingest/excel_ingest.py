"""
Excel ingestion module for VFX Ledger AI platform.
Responsible for loading production data into the ML pipeline.
"""

import pandas as pd


def load_excel(path: str) -> pd.DataFrame:
    """Load production dataset"""
    df = pd.read_excel(path)
    return df


if __name__ == "__main__":
    print("Excel ingest module ready.")
