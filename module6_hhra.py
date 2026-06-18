"""
Module 6: Human Health Risk Assessment (US EPA RAGS)
========================================================
Computes the Chronic Daily Intake (CDI), Hazard Quotient (HQ), and
Hazard Index (HI) for soil ingestion exposure, for both adult and child
receptors, following the US EPA Risk Assessment Guidance for Superfund
(RAGS) framework, as described in manuscript Section 2.5 / Equations 3-5.

    CDI = (C * IR * EF * ED * CF) / (BW * AT)
    HQ  = CDI / RfD
    HI  = sum(HQ_i) over all metals

NOTE ON SCOPE (per Fix 1 / Correction 1, reviewer response):
Oral carcinogenic risk (CR) is NOT computed for Cd or Pb in this module.
The US EPA IRIS database does not provide validated oral slope factors
(CSF) for Cd or Pb via the soil ingestion pathway: IRIS provides only an
inhalation unit risk for Cd, and withdrew its quantitative oral slope
factor for Pb in favour of the IEUBK blood-lead model. Risk
characterisation therefore relies exclusively on non-carcinogenic HQ/HI
values and regulatory exceedance of WHO/FAO soil quality limits (Module 2).
"""

import pandas as pd

# Exposure parameters (US EPA RAGS default residential soil ingestion)
EXPOSURE_PARAMS = {
    "adult": {"IR": 100, "EF": 350, "ED": 30, "BW": 70, "AT": 30 * 365},   # IR mg/day
    "child": {"IR": 200, "EF": 350, "ED": 6,  "BW": 15, "AT": 6 * 365},
}

CF_UNIT = 1e-6  # mg to kg conversion factor

# Oral reference doses (RfD), mg/kg/day, US EPA IRIS
RFD = {
    "Cu": 0.04,
    "Pb": 0.004,
    "Zn": 0.30,
    "Cd": 0.001,
}


def compute_cdi(mean_conc: dict, receptor: str) -> dict:
    """
    Compute Chronic Daily Intake for each metal, for a given receptor
    ('adult' or 'child'), using mean site concentrations.

    Parameters
    ----------
    mean_conc : dict
        Metal -> mean concentration (mg/kg), e.g. from Module 1 summary.
    receptor : str
        'adult' or 'child'.

    Returns
    -------
    dict
        Metal -> CDI (mg/kg/day).
    """
    p = EXPOSURE_PARAMS[receptor]
    cdi = {}
    for metal, C in mean_conc.items():
        cdi[metal] = (C * p["IR"] * p["EF"] * p["ED"] * CF_UNIT) / (p["BW"] * p["AT"])
    return cdi


def compute_hq(cdi: dict) -> dict:
    """Hazard Quotient per metal: HQ = CDI / RfD."""
    return {metal: cdi[metal] / RFD[metal] for metal in cdi if metal in RFD}


def compute_hi(hq: dict) -> float:
    """Hazard Index: sum of all HQ values."""
    return sum(hq.values())


def hhra_table(mean_conc: dict) -> pd.DataFrame:
    """
    Build the full Table 4-equivalent: CDI, HQ for adult and child,
    per metal, plus the HI row.
    """
    cdi_adult = compute_cdi(mean_conc, "adult")
    cdi_child = compute_cdi(mean_conc, "child")
    hq_adult = compute_hq(cdi_adult)
    hq_child = compute_hq(cdi_child)

    rows = []
    for metal in RFD:
        rows.append({
            "Metal": metal,
            "CDI-Adult (mg/kg/d)": f"{cdi_adult[metal]:.2e}",
            "HQ-Adult": round(hq_adult[metal], 4),
            "CDI-Child (mg/kg/d)": f"{cdi_child[metal]:.2e}",
            "HQ-Child": round(hq_child[metal], 4),
        })
    df = pd.DataFrame(rows)

    hi_adult = compute_hi(hq_adult)
    hi_child = compute_hi(hq_child)

    return df, hi_adult, hi_child


def worked_example(metal: str, C: float):
    """
    Print the worked CDI derivation for a single metal, matching the
    format inserted into manuscript Section 2.5.
    """
    p_a = EXPOSURE_PARAMS["adult"]
    p_c = EXPOSURE_PARAMS["child"]

    cdi_a = (C * p_a["IR"] * p_a["EF"] * p_a["ED"] * CF_UNIT) / (p_a["BW"] * p_a["AT"])
    cdi_c = (C * p_c["IR"] * p_c["EF"] * p_c["ED"] * CF_UNIT) / (p_c["BW"] * p_c["AT"])
    ratio = cdi_c / cdi_a

    print(f"Worked example -- {metal}, mean concentration C = {C} mg/kg:")
    print(f"  Adult CDI = ({C} x {p_a['IR']} x {p_a['EF']} x {p_a['ED']} x 1e-6) / "
          f"({p_a['BW']} x {p_a['AT']}) = {cdi_a:.3e} mg/kg/d")
    print(f"  Child CDI = ({C} x {p_c['IR']} x {p_c['EF']} x {p_c['ED']} x 1e-6) / "
          f"({p_c['BW']} x {p_c['AT']}) = {cdi_c:.3e} mg/kg/d")
    print(f"  Child/Adult ratio = {ratio:.2f}")
    expected_ratio = (p_c["IR"]/p_a["IR"]) * (p_c["ED"]/p_a["ED"]) * (p_a["BW"]/p_c["BW"]) * (p_a["AT"]/p_c["AT"])
    print(f"  Expected ratio from exposure parameters = {expected_ratio:.2f}")


if __name__ == "__main__":
    from module1_ingestion import load_and_validate, summary_report

    df = load_and_validate("data/soil_concentrations.csv")
    summary = summary_report(df)

    # Use manuscript-stated mean concentrations (Table 1, validated ground
    # truth per VALIDATION_NOTES.md; matches the values feeding Table 4)
    mean_conc = {
        "Cu": 11.55,
        "Pb": 29.33,
        "Zn": 129.7,
        "Cd": 0.69,
    }

    print("=== Module 6: Human Health Risk Assessment (HHRA) ===\n")
    worked_example("Cu", mean_conc["Cu"])
    print()

    hhra_df, hi_adult, hi_child = hhra_table(mean_conc)
    print(hhra_df.to_string(index=False))
    print()
    print(f"HI (adult) = {hi_adult:.4f}")
    print(f"HI (child) = {hi_child:.4f}")
    print()
    print("Manuscript Table 4 states:")
    print("  Cu : CDI_adult=1.58e-05, HQ_adult=0.0004, CDI_child=1.48e-04, HQ_child=0.0037")
    print("  Pb : CDI_adult=4.02e-05, HQ_adult=0.0100, CDI_child=3.75e-04, HQ_child=0.0938")
    print("  Zn : CDI_adult=1.78e-04, HQ_adult=0.0006, CDI_child=1.66e-03, HQ_child=0.0055")
    print("  Cd : CDI_adult=9.45e-07, HQ_adult=0.0009, CDI_child=8.82e-06, HQ_child=0.0088")
    print("  HI (adult) = 0.012, HI (child) = 0.112")
    print()
    print("NOTE: No oral CR computation -- US EPA IRIS provides no oral CSF for Cd/Pb.")
