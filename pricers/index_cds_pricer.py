import numpy as np
from scipy.interpolate import interp1d

class IndexCDSPricer:
    def __init__(self, notional, maturity, index_spread, recovery_rate,
                 discount_curve, hazard_rate_curve, num_names=125, defaults=0, payment_frequency=0.25):
        """
        Key Assumptions:
        Homogeneous Pool: All names in the index have the same hazard rate and recovery rate (simplification).
        Fixed Index Spread: Index spread is set by the market and known.
        Accrued Losses: Include losses due to defaults up to pricing date.
        Index Factor: Optionally adjust for notional factor if defaults have occurred.
        Notional Scaling: Based on the number of surviving names.
        Correlation: Zero Correlation among constituent assets.

        Parameters:
        - notional: total notional (e.g., 100M)
        - maturity: in years
        - index_spread: fixed index spread in bps (e.g., 60 bps)
        - recovery_rate: assumed recovery rate
        - discount_curve: {tenor: discount factor}
        - hazard_rate_curve: {tenor: hazard rate}
        - num_names: total number of names in the index
        - defaults: number of defaults that have occurred
        - payment_frequency: float, e.g. 0.25 for quarterly
        """
        self.notional = notional
        self.maturity = maturity
        self.spread = index_spread / 10000
        self.recovery_rate = recovery_rate
        self.payment_frequency = payment_frequency
        self.num_names = num_names
        self.defaults = defaults

        self.discount_curve = self._to_interp(discount_curve)
        self.hazard_rate_curve = self._to_interp(hazard_rate_curve)

    def _to_interp(self, curve_input):
        if callable(curve_input):
            return curve_input
        else:
            times = sorted(curve_input.keys())
            values = [curve_input[t] for t in times]
            return interp1d(times, values, kind='linear', fill_value='extrapolate')

    def _survival_probability(self, t):
        ts = np.linspace(0, t, 100)
        hs = self.hazard_rate_curve(ts)
        return np.exp(-np.trapz(hs, ts))

    def _discount_factor(self, t):
        return self.discount_curve(t)

    def _premium_leg(self):
        times = np.arange(self.payment_frequency, self.maturity + 1e-6, self.payment_frequency)
        premium_leg = 0.0
        for t in times:
            df = self._discount_factor(t)
            sp = self._survival_probability(t)
            premium_leg += df * sp * self.payment_frequency
        scaling = (self.num_names - self.defaults) / self.num_names
        return self.notional * self.spread * premium_leg * scaling

    def _protection_leg(self):
        times = np.linspace(0, self.maturity, 100)
        prot_leg = 0.0
        for i in range(1, len(times)):
            t0, t1 = times[i-1], times[i]
            dt = t1 - t0
            sp0 = self._survival_probability(t0)
            sp1 = self._survival_probability(t1)
            default_prob = sp0 - sp1
            df = self._discount_factor((t0 + t1) / 2)
            prot_leg += df * default_prob
        scaling = (self.num_names - self.defaults) / self.num_names
        return self.notional * (1 - self.recovery_rate) * prot_leg * scaling

    def _accrued_losses(self):
        """
        Losses already occurred due to prior defaults.
        """
        return self.notional * self.defaults / self.num_names * (1 - self.recovery_rate)

    def price(self):
        prot_leg = self._protection_leg()
        prem_leg = self._premium_leg()
        accrued = self._accrued_losses()
        return prot_leg - prem_leg - accrued
