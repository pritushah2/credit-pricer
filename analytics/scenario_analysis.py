from copy import deepcopy
import numpy as np

class ScenarioEngine:
    def __init__(self, pricer, base_discount_curve, base_hazard_curve):
        """
        Only supports shocks to base curve and discount curve as of now.
        
        pricer: a callable object with .price() method
        base_discount_curve: callable (e.g., from DiscountCurveBuilder)
        base_hazard_curve: callable (e.g., from HazardCurveBuilder)
        """
        self.base_pricer = pricer
        self.base_dc = base_discount_curve
        self.base_hc = base_hazard_curve
        self.results = {}

    def _apply_parallel_shift(self, curve, shift):
        """
        Returns a new shifted curve (parallel bump).
        """
        return lambda t: curve(t) * np.exp(-shift * t)

    def _apply_key_rate_shift(self, curve, shifts_dict):
        """
        Applies key rate shifts to specific tenors, interpolates the rest.
        `shifts_dict`: {tenor: shift in rate}
        """
        tenors = sorted(shifts_dict.keys())
        bump_factors = {t: np.exp(-shifts_dict[t] * t) for t in tenors}

        # Sample points from the original curve
        ts = np.linspace(0.01, max(tenors) + 5, 200)
        orig = np.array([curve(t) for t in ts])

        shift_interp = np.interp(ts, tenors, [bump_factors[t] for t in tenors])
        new_values = orig * shift_interp

        return lambda t: np.interp(t, ts, new_values)

    def run_scenario(self, name, dc_shift=0.0, hc_shift=0.0, 
                     dc_key_rate_shifts=None, hc_key_rate_shifts=None):
        """
        Runs a scenario and stores the result under `name`.
        """
        if dc_key_rate_shifts:
            new_dc = self._apply_key_rate_shift(self.base_dc, dc_key_rate_shifts)
        else:
            new_dc = self._apply_parallel_shift(self.base_dc, dc_shift)

        if hc_key_rate_shifts:
            new_hc = self._apply_key_rate_shift(self.base_hc, hc_key_rate_shifts)
        else:
            new_hc = self._apply_parallel_shift(self.base_hc, hc_shift)

        # Deepcopy the pricer and replace curves
        pricer = deepcopy(self.base_pricer)
        pricer.discount_curve = new_dc
        pricer.hazard_rate_curve = new_hc

        self.results[name] = pricer.price()

    def summarize(self):
        base_price = self.results.get("base", None)
        summary = {}
        for scenario, value in self.results.items():
            delta = None if base_price is None else value - base_price
            summary[scenario] = {"price": value, "delta": delta}
        return summary
