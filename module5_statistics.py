"""
Module 5: Statistical Analysis
=================================
Computes Pearson and Spearman correlation coefficients between metal pairs,
and runs the Shapiro-Wilk normality test on each metal's concentration
distribution, using scipy.stats, as described in manuscript Section 2.3.

NOTE: Non-detected (ND) values are excluded from correlation and normality
testing (pairwise complete observations), since correlating against an
arbitrarily imputed zero would distort the relationship. This means metal
pairs involving Pb/Zn/Cu (n=12, fully detected) and Cd (n=7 detected) use
different effective sample sizes, exactly as a careful statistician would
handle missing/non-detected data.
"""

import pandas as pd
import numpy as np
from scipy import stats
from itertools import combinations

METALS = ["Cu", "Pb", "Zn", "Cd"]


def correlation_matrix(df: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    """
    Compute the pairwise correlation matrix for the given metals,
    using pairwise-complete observations (NaN-aware).
    """
    sub = df[METALS]
    return sub.corr(method=method)


def pairwise_correlations(df: pd.DataFrame, bonferroni_n: int = 6) -> pd.DataFrame:
    """
    Compute Pearson r, Spearman rho, and p-values for every metal pair,
    matching the format reported in Section 3.5. Also flags significance
    under Bonferroni correction for multiple comparisons.

    Parameters
    ----------
    bonferroni_n : int
        Number of simultaneous comparisons for Bonferroni correction
        (default 6, matching the 4-choose-2 metal pairs in this study).
    """
    bonferroni_alpha = 0.05 / bonferroni_n
    rows = []
    for m1, m2 in combinations(METALS, 2):
        paired = df[[m1, m2]].dropna()
        n = len(paired)
        if n < 3:
            continue
        r_pearson, p_pearson = stats.pearsonr(paired[m1], paired[m2])
        rho_spearman, p_spearman = stats.spearmanr(paired[m1], paired[m2])
        rows.append({
            "Pair": f"{m1}-{m2}",
            "n": n,
            "Pearson r": round(r_pearson, 3),
            "p (Pearson)": round(p_pearson, 4),
            "Spearman rho": round(rho_spearman, 3),
            "p (Spearman)": round(p_spearman, 4),
            "|Delta rho|": round(abs(r_pearson - rho_spearman), 3),
            f"Sig. (Bonferroni, alpha={bonferroni_alpha:.4f})": "Yes" if p_pearson < bonferroni_alpha else "No",
        })
    return pd.DataFrame(rows)


def shapiro_wilk_normality(df: pd.DataFrame) -> pd.DataFrame:
    """Run Shapiro-Wilk normality test on each metal's detected values."""
    rows = []
    for metal in METALS:
        vals = df[metal].dropna()
        if len(vals) < 3:
            continue
        w_stat, p_val = stats.shapiro(vals)
        rows.append({
            "Metal": metal,
            "n": len(vals),
            "W": round(w_stat, 2),
            "p": round(p_val, 4),
            "Normal? (p>0.05)": "Yes" if p_val > 0.05 else "No",
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from module1_ingestion import load_and_validate

    df = load_and_validate("data/soil_concentrations.csv")

    print("=== Module 5: Pairwise Correlations (Pearson & Spearman) ===")
    pw = pairwise_correlations(df)
    print(pw.to_string(index=False))
    print()

    print("=== Shapiro-Wilk Normality Test ===")
    sw = shapiro_wilk_normality(df)
    print(sw.to_string(index=False))
    print()

    print("Manuscript Section 3.5 states:")
    print("  Cu-Zn : r = 0.791 (p<0.01)")
    print("  Cu-Cd : r = 0.773 (p<0.01)")
    print("  Cu-Pb : r = -0.718 (p<0.01)")
    print("  Pb-Zn : r = -0.611 (p<0.05)")
    print("  Zn-Cd : r = 0.681 (p<0.05)")
    print("  Spearman |Delta rho| <= 0.08 vs Pearson, for all pairs")
    print("  Shapiro-Wilk: Cd W=0.73 (p<0.01), Pb W=0.81 (p<0.05)")
