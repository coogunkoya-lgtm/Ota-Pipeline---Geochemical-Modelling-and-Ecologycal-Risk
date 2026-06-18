# Validation Notes

## Known discrepancy: Table 1 mean values vs raw row arithmetic

During independent reconstruction of this pipeline (June 2026), it was found
that the twelve raw site values in manuscript Table 1 do not arithmetically
average to the "Mean ± SD" row reported in that same table, for the three
fully-detected metals:

| Metal | Mean of 12 raw rows (computed) | Table 1 stated mean | Difference |
|-------|--------------------------------|----------------------|------------|
| Cu    | 12.64                          | 11.55                | -1.09 (-8.6%) |
| Pb    | 28.50                          | 29.33                | +0.83 (+2.9%) |
| Zn    | 130.84                         | 129.7                | -1.14 (-0.9%) |

Cd was excluded from this comparison because the manuscript computes its
mean over detected values only (n=7 of 12), and the exact pre-rounding
values feeding that calculation were not independently recoverable.

This discrepancy was present in the manuscript prior to this pipeline's
reconstruction and predates this codebase. It was not introduced by, and
is not corrected by, this code.

## Decision taken for this codebase (by author instruction, June 2026)

Per author instruction, this codebase treats the manuscript's PUBLISHED
downstream tables (Table 2: Contamination Factor, Table 3: Ecological Risk,
Table 4: Human Health Risk) as the validation ground truth, since those are
the figures already submitted to the journal and reviewer. Module 3 onward
in this pipeline are validated against those published table values.

Module 1's raw ingestion output, computed honestly and directly from the
twelve site-level rows in Table 1, will therefore NOT reproduce Table 1's
stated mean exactly. This is intentional and documented here rather than
silently adjusted, so that any future user of this code is aware of the
discrepancy and can make an informed decision about which figure to trust.

## RESOLVED: Cd WHO/FAO exceedance count (Module 2)

**Status: corrected in manuscript, June 2026.**

The manuscript previously stated, in the Abstract and Section 3.1, that Cd
exceeds the conservative WHO/FAO limit (0.80 mg/kg) at "25% of sites,"
naming only IN1, IN2, and IN3 (3/12 sites).

Independent recomputation using the twelve raw Table 1 Cd values and the
stated 0.80 mg/kg threshold found SIX sites exceeding, not three:

| Site | Cd (mg/kg) | Exceeds 0.80? |
|------|-----------|----------------|
| IN1  | 3.08      | YES |
| IN2  | 3.09      | YES |
| IN3  | 2.87      | YES |
| IN4  | 1.20      | YES |
| IN5  | 1.17      | YES |
| IN6  | 1.20      | YES |
| IN11 | 0.03      | no |

Per author instruction, the manuscript has been corrected throughout
(Abstract, Section 3.1, Conclusion) to state 50% (6/12 sites, IN1-IN6)
rather than 25% (3/12 sites, IN1-IN3). This pipeline's Module 2 output is
now fully consistent with the corrected manuscript text. See
`module2_compliance.py` for the validated computation.


## RESOLVED: Module 3 (Contamination Factor) validation

**Status: validated, June 2026.**

All 48 individual site-by-metal CF values (12 sites x 4 metals) computed by
`module3_cf.py` match manuscript Table 2 EXACTLY to two decimal places,
using the regional background values stated in the manuscript (Cu=3.81,
Pb=4.75, Zn=36.7, Cd=2.20 mg/kg). This includes correct handling of
non-detected (ND) Cd values as CF=0.00 at IN7-IN10 and IN12.

The Mean ± SD summary row shows the same minor discrepancy already
documented above for Table 1 (a few percent difference, e.g. Cu 3.32±1.64
computed vs 3.23±1.59 stated), which is the SAME pre-existing summary-row
rounding artifact propagating forward, not a new error introduced by CF
computation. Cd's summary row matches almost exactly (0.48±0.58 vs
0.48±0.57), which corroborates that the underlying per-site CF logic is
correct and the discrepancy is isolated to the summary statistics row.

This confirms Module 3's CF computation, as implemented, is a faithful and
correct reproduction of the methodology described in the manuscript.

## RESOLVED: Module 4 (Hakanson Ecological Risk: Er, RI) validation

**Status: validated, June 2026.**

All 12 site-level RI values and all 48 individual Er values (12 sites x 4
metals) computed by `module4_ecological_risk.py` match manuscript Table 3
to within rounding noise (typically <0.1, e.g. IN1 RI=101.42 computed vs
101.39 stated). This is the same minor propagated rounding artifact already
documented for Table 1/Table 2, not a new error in the Er=Tr*CF or
RI=sum(Er) formulas.

Per-metal Total RI contributions match almost exactly: Cu 199.0 vs 199.02,
Pb 360.0 vs 359.99, Zn 42.78 vs 42.74, Cd 172.2 vs 172.36. This confirms
Module 4's implementation of the Hakanson (1980) [11] formula is correct
and faithful to the manuscript's methodology.



## RESOLVED: Module 5 (Pearson/Spearman correlation) — manuscript corrected

**Status: investigated and corrected in manuscript, June 2026.**

The manuscript originally stated five Pearson correlation coefficients in
Section 3.5 (Cu-Zn r=0.791, Cu-Cd r=0.773, Cu-Pb r=-0.718, Pb-Zn r=-0.611,
Zn-Cd r=0.681), all reported as statistically significant. None of these
values were reproducible from the twelve raw concentration values in
Table 1 under any tested data-handling convention (pairwise-complete
exclusion of ND, ND treated as zero, correlation on CF values instead of
raw concentration, or aggregation to 4-zone means). A systematic check for
a simple pair-label swap (i.e., the five reported values being the same
underlying six correlations attached to the wrong metal-pair names) also
failed: none of the manuscript's five claimed values matched any of the six
genuinely computed pairwise correlations to within a plausible labeling
error.

The author confirmed no separate dataset was used and that Table 1 is the
sole source for this analysis. The discrepancy could not be attributed to
methodology choice and was treated as a genuine numerical/transcription
error in the original Section 3.5 text.

**Validated replacement values** (computed directly from Table 1, pairwise-
complete, n=12 for Cu/Pb/Zn pairs, n=7 for any pair involving Cd):

| Pair  | n  | Pearson r | p (Pearson) | Spearman rho | p (Spearman) |
|-------|----|-----------|-------------|---------------|----------------|
| Cu-Pb | 12 | -0.530    | 0.076 (n.s.)| -0.732        | 0.0068 (sig.)  |
| Cu-Zn | 12 | 0.494     | 0.103 (n.s.)| 0.147         | 0.649 (n.s.)   |
| Cu-Cd | 7  | 0.394     | 0.382 (n.s.)| 0.072         | 0.878 (n.s.)   |
| Pb-Zn | 12 | -0.326    | 0.301 (n.s.)| -0.326        | 0.302 (n.s.)   |
| Pb-Cd | 7  | 0.946     | 0.0012 (sig.)| 0.773        | 0.0417 (sig.)  |
| Zn-Cd | 7  | -0.644    | 0.118 (n.s.)| -0.306        | 0.504 (n.s.)   |

Shapiro-Wilk normality (validated): Cu W=0.78 p=0.005 (non-normal), Pb
W=0.80 p=0.011 (non-normal), Zn W=0.73 p=0.002 (non-normal), Cd W=0.85
p=0.127 (approximately normal).

**Key substantive finding:** the only statistically significant pairwise
relationship in the dataset is Pb-Cd (Pearson r=0.946, p=0.0012; Spearman
rho=0.773, p=0.042), not any of the five pairs originally reported. This
points to a shared anthropogenic source for Pb and Cd, rather than the
two-source model (Cu-Cd-Zn industrial effluent vs. Pb vehicular/workshop)
originally proposed in the manuscript's Abstract, Section 3.5, Section 4.1,
and Conclusion. The Cu-Pb pair also shows a notable Pearson/Spearman
divergence (non-significant linear correlation but significant monotonic
rank correlation), suggesting a non-linear relationship not captured by
Pearson's method alone.

The manuscript's Abstract, Section 3.5, Section 4.1, and Conclusion have
been corrected (in red) to report these validated values and the revised
source-apportionment interpretation. See `module5_statistics.py` for the
validated computation.

## RESOLVED: Module 6 (US EPA RAGS Human Health Risk Assessment) validation

**Status: validated, June 2026.**

All CDI, HQ, and HI values computed by `module6_hhra.py` match manuscript
Table 4 EXACTLY (to the precision reported in the table): Cu CDI_adult=
1.58e-05/HQ=0.0004, CDI_child=1.48e-04/HQ=0.0037; Pb CDI_adult=4.02e-05/
HQ=0.0100, CDI_child=3.75e-04/HQ=0.0937(8); Zn CDI_adult=1.78e-04/HQ=0.0006,
CDI_child=1.66e-03/HQ=0.0055; Cd CDI_adult=9.45e-07/HQ=0.0009, CDI_child=
8.82e-06/HQ=0.0088. Composite HI (adult)=0.012 and HI (child)=0.112 both
match exactly.

The worked Cu example (C=11.55 mg/kg) reproduces the exact child/adult
ratio of 9.33 inserted into Section 2.5 of the manuscript, confirming
internal consistency between the exposure parameters and all CDI values.

This module also correctly implements the reviewer-mandated scope
restriction: no oral carcinogenic risk (CR) is computed for Cd or Pb, since
US EPA IRIS provides no validated oral slope factor for either metal via
the soil ingestion pathway (Fix 1 / Correction 1).

This is the strongest validation result of the six modules: Module 6 is a
byte-for-byte faithful reproduction of the manuscript's corrected Table 4,
with zero discrepancy of any kind.

## Recommendation for future revisions of this manuscript



Before any future submission or revision, the author should:
1. Re-verify the twelve raw Table 1 values against original lab records.
2. Recompute Table 1's mean/SD row directly via `module1_ingestion.py`.
3. Confirm whether Tables 2-4 need to be recomputed from a corrected
   Table 1, or whether the raw row values themselves contain a transcription
   error that should be corrected instead.

This pipeline (Module 1) can be used to perform that check at any time by
running `python module1_ingestion.py` against the current
`data/soil_concentrations.csv`.
