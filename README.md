# Ota Heavy Metals Python Pipeline

A six-module Python pipeline for geochemical contamination indexing and
human health risk assessment of heavy metals in agricultural soils,
developed for:

> Ogunkoya, C. O. "Geochemical Modelling and Ecological Risk of Heavy
> Metals in Industrial Agricultural Soils: A Python-Driven Approach from
> Southwestern Nigeria." (manuscript under revision, African Scientific
> Reports / target journal)

## What this pipeline does

Given a single CSV of raw soil metal concentrations (Cu, Pb, Zn, Cd, Hg),
this pipeline computes:

1. **Module 1 (`module1_ingestion.py`)** — data validation and detection-limit flagging
2. **Module 2 (`module2_compliance.py`)** — WHO/FAO permissible limit screening
3. **Module 3 (`module3_cf.py`)** — Contamination Factor (CF)
4. **Module 4 (`module4_ecological_risk.py`)** — Hakanson (1980) ecological risk factor (Er) and Risk Index (RI)
5. **Module 5 (`module5_statistics.py`)** — Pearson/Spearman correlation and Shapiro-Wilk normality testing, with Bonferroni multiple-comparison correction
6. **Module 6 (`module6_hhra.py`)** — US EPA RAGS human health risk assessment (CDI, HQ, HI) for adult and child receptors

## Important scope note

This pipeline does **not** compute oral carcinogenic risk (CR) for Cd or
Pb. The US EPA IRIS database does not provide a validated oral slope
factor (CSF) for either metal via the soil ingestion pathway: IRIS
provides only an inhalation unit risk for cadmium, and withdrew its
quantitative oral slope factor for lead in favour of the IEUBK blood-lead
model. Risk characterisation in this pipeline relies exclusively on the
non-carcinogenic Hazard Quotient (HQ) / Hazard Index (HI) framework and
regulatory exceedance of WHO/FAO soil quality limits.

## Quick start

```bash
pip install pandas numpy scipy pytest
python run_pipeline.py data/soil_concentrations.csv
```

This writes six CSV files to `outputs/`, one per module, and prints a
consolidated console report.

## Running the tests

```bash
python -m pytest tests/test_pipeline.py -v
```

25 unit tests validate every module's output against the manuscript's
published tables. See `VALIDATION_NOTES.md` for the full validation
history, including discrepancies between earlier manuscript
drafts and the underlying data that were identified and corrected during
this pipeline's development.

## Data format

Input CSV columns: `Location, Cu, Pb, Zn, Cd, Hg` (all concentrations in
mg/kg). Non-detected values should be recorded as the string `ND`.

## Honesty note on validation

This codebase was reconstructed from the manuscript's methodology
description rather than recovered from original project files (the
original scripts were not retained). Every module was independently
validated against the manuscript's own published tables before being
considered correct. Three discrepancies were found between the
manuscript's narrative claims and what the underlying Table 1 data
actually supports; all three were investigated, confirmed, and corrected
in the manuscript itself before this
repository was finalised. Full details are in `VALIDATION_NOTES.md`.

## License

MIT License. Free to use, modify, and redistribute for academic and
research purposes.

## Citation

If you use this pipeline, please cite the associated manuscript (citation
details to be finalised on journal acceptance) and this repository's
Zenodo DOI (to be assigned on first release).
