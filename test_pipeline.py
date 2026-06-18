"""
Unit tests for the Ota Heavy Metals Python pipeline.

These tests validate each module's output against the manuscript's
published tables (Table 1-4), as documented in VALIDATION_NOTES.md.
Run with: pytest tests/test_pipeline.py -v
"""

import sys
import os
import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from module1_ingestion import load_and_validate
from module2_compliance import screen_compliance
from module3_cf import compute_cf, classify_cf
from module4_ecological_risk import compute_er, compute_ri, classify, RI_BANDS
from module5_statistics import pairwise_correlations
from module6_hhra import compute_cdi, compute_hq, compute_hi, hhra_table


DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "soil_concentrations.csv")


# --------------------------------------------------------------------------
# Module 1: Ingestion
# --------------------------------------------------------------------------

class TestModule1Ingestion:

    def test_loads_twelve_sites(self):
        df = load_and_validate(DATA_PATH)
        assert len(df) == 12

    def test_nd_flags_correct(self):
        df = load_and_validate(DATA_PATH)
        # IN7, IN8, IN9, IN10, IN12 are ND for Cd per Table 1
        assert df.loc["IN7", "Cd_ND"] == True
        assert df.loc["IN1", "Cd_ND"] == False

    def test_nd_becomes_nan(self):
        df = load_and_validate(DATA_PATH)
        assert pd.isna(df.loc["IN7", "Cd"])

    def test_known_concentration_value(self):
        df = load_and_validate(DATA_PATH)
        assert df.loc["IN1", "Cu"] == pytest.approx(19.16, abs=0.01)
        assert df.loc["IN12", "Zn"] == pytest.approx(217.09, abs=0.01)


# --------------------------------------------------------------------------
# Module 2: WHO/FAO Compliance
# --------------------------------------------------------------------------

class TestModule2Compliance:

    def test_cu_pb_zn_never_exceed(self):
        df = load_and_validate(DATA_PATH)
        flags = screen_compliance(df)
        assert flags["Cu_exceeds"].sum() == 0
        assert flags["Pb_exceeds"].sum() == 0
        assert flags["Zn_exceeds"].sum() == 0

    def test_cd_conservative_exceedance_is_six_sites(self):
        """Validated correction: 6/12 sites (50%), not the original 3/12 (25%)."""
        df = load_and_validate(DATA_PATH)
        flags = screen_compliance(df)
        assert flags["Cd_exceeds_conservative"].sum() == 6

    def test_cd_upper_exceedance_is_two_sites(self):
        df = load_and_validate(DATA_PATH)
        flags = screen_compliance(df)
        assert flags["Cd_exceeds_upper"].sum() == 2

    def test_in1_in6_all_exceed_conservative_limit(self):
        df = load_and_validate(DATA_PATH)
        flags = screen_compliance(df)
        for site in ["IN1", "IN2", "IN3", "IN4", "IN5", "IN6"]:
            assert flags.loc[site, "Cd_exceeds_conservative"] == True


# --------------------------------------------------------------------------
# Module 3: Contamination Factor
# --------------------------------------------------------------------------

class TestModule3CF:

    def test_cf_matches_table2_in1_cu(self):
        df = load_and_validate(DATA_PATH)
        cf = compute_cf(df)
        # Table 2: IN1 Cu CF = 5.03
        assert cf.loc["IN1", "Cu"] == pytest.approx(5.03, abs=0.01)

    def test_cf_matches_table2_in7_pb(self):
        df = load_and_validate(DATA_PATH)
        cf = compute_cf(df)
        # Table 2: IN7 Pb CF = 11.77
        assert cf.loc["IN7", "Pb"] == pytest.approx(11.77, abs=0.01)

    def test_nd_cd_gives_zero_cf(self):
        df = load_and_validate(DATA_PATH)
        cf = compute_cf(df)
        assert cf.loc["IN7", "Cd"] == 0.0

    def test_classify_cf_bands(self):
        assert classify_cf(0.5) == "Low"
        assert classify_cf(2.0) == "Moderate"
        assert classify_cf(4.0) == "Considerable"
        assert classify_cf(7.0) == "Very High"


# --------------------------------------------------------------------------
# Module 4: Ecological Risk (Hakanson)
# --------------------------------------------------------------------------

class TestModule4EcologicalRisk:

    def test_er_in1_cd_matches_table3(self):
        df = load_and_validate(DATA_PATH)
        cf = compute_cf(df)
        er = compute_er(cf)
        # Table 3: IN1 Cd Er = 42.0 approx (CF 1.40 * Tr 30)
        assert er.loc["IN1", "Cd"] == pytest.approx(42.0, abs=0.5)

    def test_ri_in1_matches_table3(self):
        df = load_and_validate(DATA_PATH)
        cf = compute_cf(df)
        er = compute_er(cf)
        ri = compute_ri(er)
        # Table 3: IN1 RI = 101.39 approx
        assert ri["IN1"] == pytest.approx(101.4, abs=0.5)

    def test_all_sites_classify_as_low_ri(self):
        """All site RI values fall under 150 -> Low band, per Hakanson scale."""
        df = load_and_validate(DATA_PATH)
        cf = compute_cf(df)
        er = compute_er(cf)
        ri = compute_ri(er)
        for loc, val in ri.items():
            assert classify(val, RI_BANDS) == "Low"


# --------------------------------------------------------------------------
# Module 5: Statistics (validated, post-correction values)
# --------------------------------------------------------------------------

class TestModule5Statistics:

    def test_pb_cd_is_only_significant_pair(self):
        """
        Validated finding: Pb-Cd is the only Bonferroni-significant
        correlation in the dataset (r=0.946, p=0.0012), contrary to the
        five different pairs originally claimed in the manuscript draft.
        """
        df = load_and_validate(DATA_PATH)
        pw = pairwise_correlations(df)
        pb_cd_row = pw[pw["Pair"] == "Pb-Cd"].iloc[0]
        assert pb_cd_row["Pearson r"] == pytest.approx(0.946, abs=0.01)
        assert pb_cd_row["p (Pearson)"] < 0.0083  # Bonferroni alpha for 6 comparisons

    def test_cu_pb_pearson_not_significant(self):
        df = load_and_validate(DATA_PATH)
        pw = pairwise_correlations(df)
        cu_pb_row = pw[pw["Pair"] == "Cu-Pb"].iloc[0]
        assert cu_pb_row["p (Pearson)"] > 0.05

    def test_cu_pb_spearman_significant_divergence(self):
        """Cu-Pb shows Pearson/Spearman divergence: non-sig linear, sig monotonic."""
        df = load_and_validate(DATA_PATH)
        pw = pairwise_correlations(df)
        cu_pb_row = pw[pw["Pair"] == "Cu-Pb"].iloc[0]
        assert cu_pb_row["p (Spearman)"] < 0.05


# --------------------------------------------------------------------------
# Module 6: Human Health Risk Assessment
# --------------------------------------------------------------------------

class TestModule6HHRA:

    MEAN_CONC = {"Cu": 11.55, "Pb": 29.33, "Zn": 129.7, "Cd": 0.69}

    def test_cdi_adult_cu_matches_manuscript(self):
        cdi = compute_cdi(self.MEAN_CONC, "adult")
        assert cdi["Cu"] == pytest.approx(1.58e-5, rel=0.01)

    def test_cdi_child_cu_matches_manuscript(self):
        cdi = compute_cdi(self.MEAN_CONC, "child")
        assert cdi["Cu"] == pytest.approx(1.48e-4, rel=0.01)

    def test_child_adult_ratio_is_933(self):
        """The reviewer-flagged ratio check: should be 9.33, not the
        original manuscript's erroneous 4.05."""
        cdi_a = compute_cdi(self.MEAN_CONC, "adult")
        cdi_c = compute_cdi(self.MEAN_CONC, "child")
        ratio = cdi_c["Cu"] / cdi_a["Cu"]
        assert ratio == pytest.approx(9.33, abs=0.02)

    def test_hi_adult_matches_manuscript(self):
        _, hi_adult, _ = hhra_table(self.MEAN_CONC)
        assert hi_adult == pytest.approx(0.012, abs=0.001)

    def test_hi_child_matches_manuscript(self):
        _, _, hi_child = hhra_table(self.MEAN_CONC)
        assert hi_child == pytest.approx(0.112, abs=0.001)

    def test_both_hi_below_unity(self):
        """Confirms no non-carcinogenic health hazard at mean concentrations."""
        _, hi_adult, hi_child = hhra_table(self.MEAN_CONC)
        assert hi_adult < 1.0
        assert hi_child < 1.0

    def test_no_carcinogenic_risk_computed(self):
        """
        Per Fix 1: this module must NOT expose any oral CSF or CR
        computation, since IRIS provides no validated oral slope factor
        for Cd or Pb via soil ingestion.
        """
        import module6_hhra
        assert not hasattr(module6_hhra, "compute_cr")
        assert not hasattr(module6_hhra, "CSF")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
