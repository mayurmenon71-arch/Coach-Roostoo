"""
Offline tests for the fee hurdle (breakeven-alpha) calculator — deterministic,
NO API key required. Guards the paper's core invariant: the fee number is exact,
reproducible, and gate-consistent (Rules to Rewards v1.2, Sections 7.6 / 8.1).

Run:  python3 -m unittest tests.test_breakeven
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from coach_compiler import breakeven as B
from coach_compiler import schema as S
from coach_compiler.genecard import build_gene_card


class TestCostModel(unittest.TestCase):
    def test_round_trip_cost_matches_paper(self):
        # 2 x 4.0 taker + 1.5 spread + 1.0 slippage = 10.5 bps ("~9-12 bps").
        self.assertAlmostEqual(B.ROUND_TRIP_COST_BPS, 10.5, places=6)

    def test_paper_worked_example(self):
        # Section 8.1: 4 flips/day x ~10 bps ~= 40 bps/day ~= ~12%/month.
        # 4 round trips/hr is far above any cadence cap, so this exercises the
        # raw arithmetic via a per-day count instead.
        h = B._hurdle(4.0, "5m")
        self.assertAlmostEqual(h["cost_bps_per_day"], 42.0, places=6)   # 4 x 10.5
        self.assertAlmostEqual(h["monthly_hurdle_pct"], 12.6, places=6)  # ~12%/mo
        self.assertEqual(h["fee_drag"], "High")

    def test_monotonic_in_turnover(self):
        prev = -1.0
        for rt in (0.5, 1.0, 2.0, 4.0, 8.0):
            m = B._hurdle(rt, "5m")["monthly_hurdle_pct"]
            self.assertGreater(m, prev)
            prev = m

    def test_fee_drag_tiers(self):
        self.assertEqual(B.fee_drag_label(10.0), "Low")       # <= 25
        self.assertEqual(B.fee_drag_label(25.0), "Low")       # boundary
        self.assertEqual(B.fee_drag_label(30.0), "Moderate")  # 25-40
        self.assertEqual(B.fee_drag_label(40.0), "Moderate")  # boundary
        self.assertEqual(B.fee_drag_label(41.0), "High")      # > 40 -> screen


class TestBreakevenCalcPrimitive(unittest.TestCase):
    def test_capped_by_cadence_steps(self):
        # An absurd turnover ceiling can't exceed the physical step count/day.
        h = B.breakeven_calc("15m", 1000.0)
        self.assertLessEqual(h["round_trips_per_day"], B.DECISION_STEPS_PER_DAY["15m"])

    def test_rejects_unknown_interval(self):
        with self.assertRaises(ValueError):
            B.breakeven_calc("3m", 1.0)

    def test_rejects_negative_turnover(self):
        with self.assertRaises(ValueError):
            B.breakeven_calc("5m", -1.0)

    def test_zero_turnover_is_free(self):
        h = B.breakeven_calc("5m", 0.0)
        self.assertEqual(h["cost_bps_per_day"], 0.0)
        self.assertEqual(h["fee_drag"], "Low")
        self.assertTrue(h["passes_screen"])


class TestConfigEstimate(unittest.TestCase):
    def test_every_archetype_and_interval(self):
        for arch in S.ARCHETYPES:
            for interval in ("15m", "5m", "1m"):
                cfg = {"candle_interval": interval}
                h = B.estimate_for_config(cfg, arch)
                self.assertIn(h["fee_drag"], ("Low", "Moderate", "High"))
                self.assertGreater(h["monthly_hurdle_pct"], 0)
                self.assertTrue(h["explanation"])
                self.assertIn("passes_screen", h)

    def test_faster_clock_costs_more(self):
        for arch in S.ARCHETYPES:
            slow = B.estimate_for_config({"candle_interval": "15m"}, arch)
            fast = B.estimate_for_config({"candle_interval": "1m"}, arch)
            self.assertGreater(fast["cost_bps_per_day"], slow["cost_bps_per_day"])

    def test_momentum_15m_is_low_drag(self):
        # Section 6 fee-drag column: momentum = Low.
        h = B.estimate_for_config({"candle_interval": "15m"}, "intraday_momentum")
        self.assertEqual(h["fee_drag"], "Low")
        self.assertTrue(h["passes_screen"])

    def test_fast_mean_reversion_trips_screen(self):
        # "The most fee-fragile arena archetype"; 1m cadence should fail the
        # breakeven screen and carry a warning to surface.
        h = B.estimate_for_config({"candle_interval": "1m"}, "mean_reversion")
        self.assertEqual(h["fee_drag"], "High")
        self.assertFalse(h["passes_screen"])
        self.assertIn("warning", h)

    def test_unknown_archetype_falls_back(self):
        h = B.estimate_for_config({"candle_interval": "5m"}, None)
        self.assertGreater(h["cost_bps_per_day"], 0)
        self.assertEqual(h["archetype_label"], "trading")

    def test_bad_interval_falls_back_to_5m(self):
        h = B.estimate_for_config({"candle_interval": "1h"}, "breakout")
        self.assertEqual(h["decision_interval"], "5m")

    def test_deterministic(self):
        cfg = {"candle_interval": "5m"}
        a = B.estimate_for_config(cfg, "flow_driven")
        b = B.estimate_for_config(cfg, "flow_driven")
        self.assertEqual(a, b)


class TestGeneCardIntegration(unittest.TestCase):
    def _card(self, config, archetype):
        return build_gene_card(config, {}, {"archetype": archetype})

    def test_card_carries_breakeven_fields(self):
        cfg = S.default_config_for("intraday_momentum", assets=["BTCUSDT"])
        card = self._card(cfg, "intraday_momentum")
        self.assertIn("breakeven", card)
        self.assertIn("fee_drag", card)
        self.assertEqual(card["archetype"], "momentum")   # friendly, never the raw id
        self.assertTrue(card["breakeven"]["explanation"])

    def test_high_drag_config_adds_warning(self):
        cfg = S.default_config_for("mean_reversion", assets=["SOLUSDT"])
        cfg["candle_interval"] = "1m"
        card = self._card(cfg, "mean_reversion")
        self.assertEqual(card["fee_drag"], "High")
        self.assertTrue(any(w.get("path") == "fee_hurdle" for w in card["warnings"]))

    def test_low_drag_config_has_no_fee_warning(self):
        cfg = S.default_config_for("intraday_momentum", assets=["BTCUSDT"])
        card = self._card(cfg, "intraday_momentum")
        self.assertFalse(any(w.get("path") == "fee_hurdle" for w in card["warnings"]))

    def test_never_leaks_underscored_archetype_id(self):
        # TONE bans raw ids like "intraday_momentum"; a plain word ("breakout")
        # is fine. Guard against the underscored ids leaking to the UI.
        for arch in S.ARCHETYPES:
            cfg = S.default_config_for(arch, assets=["BTCUSDT"])
            card = self._card(cfg, arch)
            self.assertNotIn("_", card["archetype"])


class TestScalpingRefusal(unittest.TestCase):
    def test_numbers_present_and_exact(self):
        r = B.scalping_refusal_numbers()
        self.assertAlmostEqual(r["round_trip_cost_bps"], 10.5, places=6)
        self.assertEqual(r["per_minute_day_bps"], 10.5 * 60 * 24)
        self.assertIn("bps", r["example"])


if __name__ == "__main__":
    unittest.main()
