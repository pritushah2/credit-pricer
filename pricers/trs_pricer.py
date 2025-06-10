# pricers/trs_pricer.py

import numpy as np
from scipy.interpolate import interp1d

class TRSPricer:
    def __init__(self, notional, maturity, spread, coupon_rate, 
                 recovery_rate, discount_curve, hazard_rate_curve, 
                 financing_rate=0.03, payment_frequency=0.25):
        """
        Key Assumptions:
        The TRS is on a corporate bond.
        We hold until maturity.
        Payments are discrete (e.g., quarterly).
        Flat financing rate over tenor (can later extend to curve-based).
        
        Parameters:
        - notional: float
        - maturity: in years
        - spread: TRS spread (bps, paid over financing leg)
        - coupon_rate: bond coupon (annualized, e.g., 0.05 = 5%)
        - recovery_rate: assumed recovery on default
        - discount_curve: {tenor: df}
        - hazard_rate_curve: {tenor: hazard rate}
        - financing_rate: annualized rate paid on notional (e.g., 3%)
        - payment_frequency: float (e.g., 0.25 for quarterly)
        """
        self.notional = notional
        self.maturity = maturity
        self.spread = spread / 10000  # convert bps to decimal
        self.coupon_rate = coupon_rate
        self.recovery_rate = recovery_rate
        self.financing_rate = financing_rate
        self.payment_frequency = payment_frequency

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

    def _expected_price(self, t):
        """Expected bond price at time t"""
        sp = self._survival_probability(t)
        return sp + (1 - sp) * self.recovery_rate

    def _total_return_leg(self):
        """
        Return = Coupon Income + Price Change (expected terminal value - current price)
        """
        # Expected terminal bond value
        terminal_price = self._expected_price(self.maturity)

        # Coupon leg (received)
        times = np.arange(self.payment_frequency, self.maturity + 1e-6, self.payment_frequency)
        coupons = 0.0
        for t in times:
            df = self._discount_factor(t)
            sp = self._survival_probability(t)
            coupons += df * sp * self.coupon_rate * self.payment_frequency

        # Terminal value (bond is worth expected_price at maturity)
        df_term = self._discount_factor(self.maturity)
        terminal_val = df_term * terminal_price

        return self.notional * (coupons + terminal_val)

    def _financing_leg(self):
        """
        Pay financing cost + TRS spread
        """
        times = np.arange(self.payment_frequency, self.maturity + 1e-6, self.payment_frequency)
        total_cost = 0.0
        rate = self.financing_rate + self.spread
        for t in times:
            df = self._discount_factor(t)
            total_cost += df * rate * self.payment_frequency
        return self.notional * total_cost

    def price(self):
        return self._total_return_leg() - self._financing_leg()
