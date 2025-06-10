from copy import deepcopy
import numpy as np

class SensitivityEngine:
    def __init__(self, pricer, base_discount_curve, base_hazard_curve):
        """
        pricer: pricing object with .price()
        base_discount_curve: callable
        base_hazard_curve: callable
        """
        self.pricer = pricer
        self.base_dc = base_discount_curve
        self.base_hc = base_hazard_curve
        self.base_price = pricer.price()

    def _bump_curve(self, curve, bump_bp, tenor=None):
        """
        Applies a bump to a curve. If tenor is None, bumps all points (parallel).
        Otherwise applies key rate bump using Gaussian bump at the target tenor.
        """
        bump_decimal = bump_bp / 10000

        ts = np.linspace(0.01, 30.0, 1000)
        values = np.array([curve(t) for t in ts])

        if tenor is None:
            # Parallel bump
            bumped = values * np.exp(-bump_decimal * ts)
        else:
            # Key rate bump: Gaussian centered at tenor
            sigma = 0.25  # controls width of the bump
            gauss = np.exp(-0.5 * ((ts - tenor) / sigma)**2)
            bump_factors = np.exp(-bump_decimal * ts * gauss)
            bumped = values * bump_factors

        return lambda t: np.interp(t, ts, bumped)

    def compute_pv01(self, bump_bp=1.0):
        """
        Computes parallel PV01 (IR and credit).
        Returns: dict with IR01, CS01
        """
        # Interest rate bump
        bumped_dc = self._bump_curve(self.base_dc, bump_bp, tenor=None)
        pricer_ir = deepcopy(self.pricer)
        pricer_ir.discount_curve = bumped_dc
        ir01 = pricer_ir.price() - self.base_price

        # Credit spread bump
        bumped_hc = self._bump_curve(self.base_hc, bump_bp, tenor=None)
        pricer_cs = deepcopy(self.pricer)
        pricer_cs.hazard_rate_curve = bumped_hc
        cs01 = pricer_cs.price() - self.base_price

        return {"IR01": ir01, "CS01": cs01}

    def compute_key_rate_sensitivities(self, tenors, bump_bp=1.0):
        """
        Computes key rate IR01 and CS01.
        Returns: dict of {tenor: (IR01, CS01)}
        """
        results = {}
        for t in tenors:
            bumped_dc = self._bump_curve(self.base_dc, bump_bp, tenor=t)
            bumped_hc = self._bump_curve(self.base_hc, bump_bp, tenor=t)

            pricer_ir = deepcopy(self.pricer)
            pricer_ir.discount_curve = bumped_dc
            ir01 = pricer_ir.price() - self.base_price

            pricer_cs = deepcopy(self.pricer)
            pricer_cs.hazard_rate_curve = bumped_hc
            cs01 = pricer_cs.price() - self.base_price

            results[t] = {"IR01": ir01, "CS01": cs01}
        return results
