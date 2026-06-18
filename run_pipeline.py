"""
run_pipeline.py
=================
Master orchestration script for the Ota Heavy Metals Python pipeline.

Runs all six modules in sequence on a single input CSV and produces a
consolidated console report plus CSV exports of every intermediate table,
matching the reproducibility claims made in the manuscript:

  "GEOCHEMICAL MODELLING AND ECOLOGICAL RISK OF HEAVY METALS IN INDUSTRIAL
   AGRICULTURAL SOILS: A PYTHON-DRIVEN APPROACH FROM SOUTHWESTERN NIGERIA"
  C. O. Ogunkoya, Ajayi Crowther University, Oyo, Nigeria.

Usage
-----
    python run_pipeline.py [path_to_csv]

If no path is given, defaults to data/soil_concentrations.csv (the
manuscript's Table 1 dataset, used throughout VALIDATION_NOTES.md).

Outputs
-------
Writes the following CSV files to outputs/:
    01_validated_concentrations.csv
    02_who_fao_compliance.csv
    03_contamination_factor.csv
    04_ecological_risk.csv
    05_correlation_matrix.csv
    06_human_health_risk.csv
"""

import sys
import os

from module1_ingestion import load_and_validate, summary_report
from module2_compliance import screen_compliance, exceedance_summary
from module3_cf import compute_cf, cf_summary
from module4_ecological_risk import compute_er, compute_ri, ri_summary, classify, RI_BANDS
from module5_statistics import pairwise_correlations, shapiro_wilk_normality
from module6_hhra import hhra_table, worked_example


MEAN_CONCENTRATIONS_FOR_HHRA = {
    "Cu": 11.55,
    "Pb": 29.33,
    "Zn": 129.7,
    "Cd": 0.69,
}


def run(csv_path: str, output_dir: str = "outputs"):
    os.makedirs(output_dir, exist_ok=True)

    print("=" * 72)
    print("OTA HEAVY METALS PYTHON PIPELINE")
    print("Geochemical Modelling and Ecological Risk Assessment")
    print("=" * 72)

    # ---------------- Module 1: Ingestion & Validation ----------------
    print("\n[Module 1] Loading and validating raw concentration data...")
    df = load_and_validate(csv_path)
    df.to_csv(os.path.join(output_dir, "01_validated_concentrations.csv"))
    print(summary_report(df).to_string(index=False))

    # ---------------- Module 2: WHO/FAO Compliance ----------------
    print("\n[Module 2] Screening against WHO/FAO permissible limits...")
    flags = screen_compliance(df)
    flags.to_csv(os.path.join(output_dir, "02_who_fao_compliance.csv"))
    print(exceedance_summary(flags, n_sites=len(df)).to_string(index=False))

    # ---------------- Module 3: Contamination Factor ----------------
    print("\n[Module 3] Computing Contamination Factor (CF)...")
    cf = compute_cf(df)
    cf.to_csv(os.path.join(output_dir, "03_contamination_factor.csv"))
    print(cf_summary(cf).to_string(index=False))

    # ---------------- Module 4: Ecological Risk (Hakanson) ----------------
    print("\n[Module 4] Computing Ecological Risk Factor (Er) and Risk Index (RI)...")
    er = compute_er(cf)
    ri = compute_ri(er)
    combined_4 = er.copy()
    combined_4["RI"] = ri
    combined_4.to_csv(os.path.join(output_dir, "04_ecological_risk.csv"))
    for loc, val in ri.items():
        print(f"  {loc}: RI = {val:6.2f}  ({classify(val, RI_BANDS)})")

    # ---------------- Module 5: Statistical Analysis ----------------
    print("\n[Module 5] Running Pearson/Spearman correlation and normality tests...")
    pw = pairwise_correlations(df)
    pw.to_csv(os.path.join(output_dir, "05_correlation_matrix.csv"), index=False)
    print(pw.to_string(index=False))
    sw = shapiro_wilk_normality(df)
    print(sw.to_string(index=False))

    # ---------------- Module 6: Human Health Risk Assessment ----------------
    print("\n[Module 6] Computing Human Health Risk Assessment (CDI, HQ, HI)...")
    print("  NOTE: oral carcinogenic risk (CR) is NOT computed -- see module docstring.")
    hhra_df, hi_adult, hi_child = hhra_table(MEAN_CONCENTRATIONS_FOR_HHRA)
    hhra_df.to_csv(os.path.join(output_dir, "06_human_health_risk.csv"), index=False)
    print(hhra_df.to_string(index=False))
    print(f"  HI (adult) = {hi_adult:.4f}   HI (child) = {hi_child:.4f}")

    print("\n" + "=" * 72)
    print(f"Pipeline complete. All intermediate tables written to '{output_dir}/'.")
    print("=" * 72)


if __name__ == "__main__":
    csv_arg = sys.argv[1] if len(sys.argv) > 1 else "data/soil_concentrations.csv"
    run(csv_arg)
