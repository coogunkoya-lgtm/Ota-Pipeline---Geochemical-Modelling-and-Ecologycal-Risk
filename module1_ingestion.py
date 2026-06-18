"""
Module 1: Data Ingestion and Validation
=========================================
Reads raw soil heavy metal concentration data (mg/kg) from a structured CSV
file and flags entries that are below the instrumental detection limit (ND).

Input
-----
A CSV file with columns: Location, Cu, Pb, Zn, Cd, Hg
Non-detected values are recorded as the string "ND".

Output
------
A pandas DataFrame with:
  - Original concentration columns (numeric, NaN where ND)
  - A boolean "<metal>_ND" flag column for every metal
"""

import pandas as pd
import numpy as np


METALS = ["Cu", "Pb", "Zn", "Cd", "Hg"]


def load_and_validate(csv_path: str) -> pd.DataFrame:
    """
    Load raw concentration data and flag non-detected (ND) values.

    Parameters
    ----------
    csv_path : str
        Path to the input CSV file.

    Returns
    -------
    pd.DataFrame
        DataFrame indexed by Location, with numeric concentration columns
        (NaN where not detected) and boolean "<metal>_ND" flag columns.
    """
    df = pd.read_csv(csv_path)

    if "Location" not in df.columns:
        raise ValueError("Input CSV must contain a 'Location' column.")

    df = df.set_index("Location")

    for metal in METALS:
        if metal not in df.columns:
            continue
        # Flag ND values BEFORE coercing to numeric
        is_nd = df[metal].astype(str).str.strip().str.upper() == "ND"
        df[f"{metal}_ND"] = is_nd
        # Coerce to numeric; ND becomes NaN
        df[metal] = pd.to_numeric(df[metal], errors="coerce")

    return df


def summary_report(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce a simple summary of detected vs non-detected counts per metal,
    and mean/SD computed over DETECTED values only (matching the
    manuscript's convention: "Mean ± SD computed for detected values only").
    """
    rows = []
    for metal in METALS:
        if metal not in df.columns:
            continue
        nd_col = f"{metal}_ND"
        n_detected = (~df[nd_col]).sum()
        n_total = len(df)
        detected_values = df.loc[~df[nd_col], metal]
        mean_val = detected_values.mean() if n_detected > 0 else np.nan
        sd_val = detected_values.std(ddof=1) if n_detected > 1 else np.nan
        rows.append({
            "Metal": metal,
            "N_detected": n_detected,
            "N_total": n_total,
            "Mean (detected only)": round(mean_val, 2) if pd.notna(mean_val) else "—",
            "SD (detected only)": round(sd_val, 2) if pd.notna(sd_val) else "—",
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = load_and_validate("data/soil_concentrations.csv")
    print("=== Module 1: Validated Dataset ===")
    print(df[["Cu", "Pb", "Zn", "Cd", "Hg"]])
    print()
    print("=== Detection Summary (matches Table 1 Mean ± SD row) ===")
    print(summary_report(df).to_string(index=False))
