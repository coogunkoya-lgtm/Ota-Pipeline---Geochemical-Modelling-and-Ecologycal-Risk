"""
Module 2: WHO/FAO Compliance Screening
========================================
Vectorized comparison of measured concentrations against WHO/FAO permissible
soil limits. Returns a site-by-metal boolean exceedance matrix and a summary
of exceedance counts, replacing manual row-by-row checking.

WHO/FAO permissible limits used (Table 1, manuscript):
  Cu : 100 mg/kg
  Pb : 70  mg/kg
  Zn : 300 mg/kg
  Cd : 0.80 mg/kg (conservative, pH < 6.0) / 3.0 mg/kg (upper, pH > 7.0)
  Hg : 0.30 mg/kg
"""

import pandas as pd
import numpy as np

WHO_FAO_LIMITS = {
    "Cu": 100.0,
    "Pb": 70.0,
    "Zn": 300.0,
    "Cd_conservative": 0.80,
    "Cd_upper": 3.0,
    "Hg": 0.30,
}


def screen_compliance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag exceedances of WHO/FAO limits for each metal at each site.

    Parameters
    ----------
    df : pd.DataFrame
        Output of Module 1 (load_and_validate), indexed by Location,
        with numeric Cu/Pb/Zn/Cd/Hg columns (NaN where ND).

    Returns
    -------
    pd.DataFrame
        Boolean exceedance flags: Cu_exceeds, Pb_exceeds, Zn_exceeds,
        Cd_exceeds_conservative, Cd_exceeds_upper, Hg_exceeds.
    """
    result = pd.DataFrame(index=df.index)

    result["Cu_exceeds"] = df["Cu"] > WHO_FAO_LIMITS["Cu"]
    result["Pb_exceeds"] = df["Pb"] > WHO_FAO_LIMITS["Pb"]
    result["Zn_exceeds"] = df["Zn"] > WHO_FAO_LIMITS["Zn"]
    result["Cd_exceeds_conservative"] = df["Cd"] > WHO_FAO_LIMITS["Cd_conservative"]
    result["Cd_exceeds_upper"] = df["Cd"] > WHO_FAO_LIMITS["Cd_upper"]
    if "Hg" in df.columns:
        result["Hg_exceeds"] = df["Hg"] > WHO_FAO_LIMITS["Hg"]

    return result


def exceedance_summary(flags: pd.DataFrame, n_sites: int) -> pd.DataFrame:
    """Summarise exceedance counts and percentage of sites exceeding."""
    rows = []
    for col in flags.columns:
        n_exceed = flags[col].sum()
        pct = round(100 * n_exceed / n_sites, 1)
        rows.append({"Flag": col, "Sites exceeding": int(n_exceed), "Percent": f"{pct}%"})
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from module1_ingestion import load_and_validate

    df = load_and_validate("data/soil_concentrations.csv")
    flags = screen_compliance(df)

    print("=== Module 2: WHO/FAO Exceedance Flags ===")
    print(flags)
    print()
    print("=== Exceedance Summary ===")
    print(exceedance_summary(flags, n_sites=len(df)).to_string(index=False))
    print()
    print("Manuscript claims (Abstract / Section 3.1, CORRECTED):")
    print("  Cd exceeds conservative limit (0.80) at 50% of sites (IN1-IN6) -> expect 6/12")
    print("  Cu, Pb, Zn remain within permissible limits -> expect 0 exceedances each")
