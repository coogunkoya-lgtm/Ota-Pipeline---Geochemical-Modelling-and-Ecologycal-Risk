"""
Module 4: Hakanson Potential Ecological Risk Assessment
===========================================================
Computes the single-element potential ecological risk factor (Er) and the
composite Risk Index (RI) at each site, following Hakanson (1980) [11].

    Er_i = T_r_i * CF_i
    RI   = sum(Er_i) over all metals at a site

Toxic-response factors (T_r), standard Hakanson values as applied in the
manuscript:
    Cu = 5, Pb = 5, Zn = 1, Cd = 30

Risk bands:
    Er  : <40 low; 40-80 moderate; 80-160 considerable; 160-320 high; >=320 very high
    RI  : <150 low; 150-300 moderate; 300-600 considerable; >=600 very high
"""

import pandas as pd

TOXIC_RESPONSE_FACTOR = {
    "Cu": 5,
    "Pb": 5,
    "Zn": 1,
    "Cd": 30,
}

ER_BANDS = [
    (40, "Low"),
    (80, "Moderate"),
    (160, "Considerable"),
    (320, "High"),
    (float("inf"), "Very High"),
]

RI_BANDS = [
    (150, "Low"),
    (300, "Moderate"),
    (600, "Considerable"),
    (float("inf"), "Very High"),
]


def compute_er(cf_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute the potential ecological risk factor (Er) for each metal at
    each site: Er_i = T_r_i * CF_i.

    Parameters
    ----------
    cf_df : pd.DataFrame
        Output of Module 3 (compute_cf), indexed by Location.

    Returns
    -------
    pd.DataFrame
        Er values per metal per site.
    """
    er = pd.DataFrame(index=cf_df.index)
    for metal, tr in TOXIC_RESPONSE_FACTOR.items():
        er[metal] = (cf_df[metal] * tr).round(2)
    return er


def compute_ri(er_df: pd.DataFrame) -> pd.Series:
    """Composite Risk Index per site: RI = sum of Er across all metals."""
    return er_df.sum(axis=1).round(2)


def classify(value: float, bands: list) -> str:
    for threshold, label in bands:
        if value < threshold:
            return label
    return bands[-1][1]


def ri_summary(er_df: pd.DataFrame, ri_series: pd.Series) -> dict:
    """
    Mean ± SD for each metal's Er and the composite RI, plus the
    per-metal "Total RI contribution" (cumulative Er across all sites),
    matching the manuscript's Table 3 summary rows.
    """
    summary = {}
    for metal in er_df.columns:
        vals = er_df[metal]
        summary[metal] = {
            "Mean ± SD": f"{vals.mean():.2f} ± {vals.std(ddof=1):.2f}",
            "Total RI contribution": round(vals.sum(), 2),
        }
    summary["RI (site)"] = {
        "Mean ± SD": f"{ri_series.mean():.1f} ± {ri_series.std(ddof=1):.1f}",
        "Total RI contribution": round(ri_series.sum(), 1),
    }
    return summary


if __name__ == "__main__":
    from module1_ingestion import load_and_validate
    from module3_cf import compute_cf

    df = load_and_validate("data/soil_concentrations.csv")
    cf = compute_cf(df)
    er = compute_er(cf)
    ri = compute_ri(er)

    print("=== Module 4: Ecological Risk Factor (Er) per metal, per site ===")
    print(er)
    print()
    print("=== Composite Site RI ===")
    print(ri)
    print()

    print("=== Summary (compare to Table 3) ===")
    summary = ri_summary(er, ri)
    for k, v in summary.items():
        print(f"  {k:12s} Mean±SD = {v['Mean ± SD']:>18s}   Total = {v['Total RI contribution']}")

    print()
    print("Manuscript Table 3 states:")
    print("  Cu : 16.59 ± 7.97   Total = 199.02")
    print("  Pb : 30.00 ± 19.65  Total = 359.99")
    print("  Zn : 3.40 ± 1.35    Total = 42.74")
    print("  Cd : 14.36 ± 17.10  Total = 172.36")
    print("  RI : 64.5 ± 24.1    Total = 773.7 (cumulative)")
    print()
    print("Per-site RI classification (band):")
    for loc, val in ri.items():
        print(f"  {loc}: RI={val:.2f} -> {classify(val, RI_BANDS)}")
