import numpy as np
from scipy.interpolate import interp1d

class CDSPricer:
    def __init__(self, notional, maturity, spread, recovery_rate, 
                 discount_curve, hazard_rate_curve, payment_frequency=0.25):
        """
        Parameters:
        - notional: float
        - maturity: float (in years)
        - spread: float (in bps, e.g. 100 = 1%)
        - recovery_rate: float (0.4 = 40%)
        - discount_curve: dict or callable {tenor: df}
        - hazard_rate_curve: dict or callable {tenor: hazard_rate}
        - payment_frequency: float (e.g., 0.25 = quarterly)
        """
        self.notional = notional
        self.maturity = maturity
        self.spread = spread / 10000  # Convert bps to decimal
        self.recovery_rate = recovery_rate
        self.payment_frequency = payment_frequency

        # Interpolate curves
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
        """S(t) = exp(-∫₀^t h(s) ds)"""
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
        return self.notional * self.spread * premium_leg

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
        return self.notional * (1 - self.recovery_rate) * prot_leg

    def price(self):
        prot_leg = self._protection_leg()
        prem_leg = self._premium_leg()
        return prot_leg - prem_leg
