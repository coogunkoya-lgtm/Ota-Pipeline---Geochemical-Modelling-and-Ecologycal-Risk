"""
Module 3: Contamination Indexing (Contamination Factor)
==========================================================
Computes the single-element Contamination Factor (CF) for each metal at
each site, relative to a regional geochemical background value.

    CF = C_sample / C_background

Classification (Hakanson, 1980 [11], as applied in the manuscript):
    CF < 1        : low contamination
    1 <= CF < 3    : moderate contamination
    3 <= CF < 6    : considerable contamination
    CF >= 6        : very high contamination

NOTE ON SCOPE (per reviewer Fix 4 / Correction 4):
Module 3 is also capable of computing Igeo (geoaccumulation index), PLI
(pollution load index), and mCd (modified degree of contamination) as
NumPy array operations on the same background-normalised data. However,
consistent with the manuscript's stated scope, only CF is computed and
reported here, since CF is the direct input to the Hakanson ecological
risk framework (Er, RI) implemented in Module 4. Igeo/PLI/mCd functions
are stubbed below for future extension but are NOT exercised by the
validated pipeline.
"""

import pandas as pd
import numpy as np

# Regional geochemical background values (mg/kg), Menkiti et al. [19]
BACKGROUND = {
    "Cu": 3.81,
    "Pb": 4.75,
    "Zn": 36.7,
    "Cd": 2.20,
}

CF_BANDS = [
    (1, "Low"),
    (3, "Moderate"),
    (6, "Considerable"),
    (float("inf"), "Very High"),
]


def compute_cf(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the Contamination Factor for Cu, Pb, Zn, Cd at each site.

    Parameters
    ----------
    df : pd.DataFrame
        Output of Module 1, indexed by Location, with numeric Cu/Pb/Zn/Cd
        columns (NaN where not detected).

    Returns
    -------
    pd.DataFrame
        CF values per metal per site. Non-detected concentrations (NaN)
        are treated as 0.00 mg/kg for CF purposes, matching the
        manuscript's convention of reporting CF = 0.00 at ND sites
        (see Table 2, IN7-IN10, IN12).
    """
    cf = pd.DataFrame(index=df.index)
    for metal, bg in BACKGROUND.items():
        conc = df[metal].fillna(0.0)
        cf[metal] = conc / bg
    return cf.round(2)


def classify_cf(value: float) -> str:
    """Return the Hakanson contamination class for a single CF value."""
    for threshold, label in CF_BANDS:
        if value < threshold:
            return label
    return "Very High"


def cf_summary(cf_df: pd.DataFrame) -> pd.DataFrame:
    """Mean ± SD and class range per metal, matching Table 2's summary row."""
    rows = []
    for metal in cf_df.columns:
        vals = cf_df[metal]
        mean_val = vals.mean()
        sd_val = vals.std(ddof=1)
        min_class = classify_cf(vals.min())
        max_class = classify_cf(vals.max())
        class_range = min_class if min_class == max_class else f"{min_class}-{max_class}"
        rows.append({
            "Metal": metal,
            "Mean ± SD": f"{mean_val:.2f} ± {sd_val:.2f}",
            "Class range": class_range,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Stubs for future extension (NOT used in the validated pipeline; see scope
# note above). Included only so the module's full documented capability is
# visible in the codebase, per reviewer Correction 4.
# ---------------------------------------------------------------------------

def compute_igeo(df: pd.DataFrame) -> pd.DataFrame:
    """Geoaccumulation index: Igeo = log2(C / (1.5 * background)). NOT REPORTED."""
    igeo = pd.DataFrame(index=df.index)
    for metal, bg in BACKGROUND.items():
        conc = df[metal].fillna(0.0).replace(0, np.nan)  # log undefined at 0
        igeo[metal] = np.log2(conc / (1.5 * bg))
    return igeo.round(2)


def compute_pli(cf_df: pd.DataFrame) -> pd.Series:
    """Pollution Load Index: PLI = (product of CF_i)^(1/n). NOT REPORTED."""
    cf_safe = cf_df.replace(0, np.nan)  # geometric mean undefined at 0
    n = cf_safe.shape[1]
    pli = cf_safe.prod(axis=1, skipna=False) ** (1.0 / n)
    return pli.round(2)


def compute_mcd(cf_df: pd.DataFrame) -> pd.Series:
    """Modified degree of contamination: mCd = sum(CF_i) / n. NOT REPORTED."""
    n = cf_df.shape[1]
    return (cf_df.sum(axis=1) / n).round(2)


if __name__ == "__main__":
    from module1_ingestion import load_and_validate

    df = load_and_validate("data/soil_concentrations.csv")
    cf = compute_cf(df)

    print("=== Module 3: Contamination Factor (CF) ===")
    print(cf)
    print()
    print("=== CF Summary (compare to Table 2 Mean ± SD row) ===")
    print(cf_summary(cf).to_string(index=False))
    print()
    print("Manuscript Table 2 states:")
    print("  Cu : 3.23 ± 1.59  (Mod.-Consid.)")
    print("  Pb : 6.00 ± 3.93  (Consid.-Very High)")
    print("  Zn : 3.40 ± 1.35  (Mod.-Very High)")
    print("  Cd : 0.48 ± 0.57  (Low-Moderate)")
