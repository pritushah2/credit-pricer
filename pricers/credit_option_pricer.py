# pricers/credit_option_pricer.py

import numpy as np
from scipy.stats import norm


class CreditOptionPricer:
    def __init__(
        self,
        notional: float,
        strike: float,             # strike spread (bps)
        maturity: float,           # option expiry (in years)
        cds_maturity: float,       # underlying CDS maturity (in years)
        spread: float,             # current forward CDS spread (bps)
        volatility: float,         # implied vol of spread (lognormal)
        option_type: str,          # "payer" or "receiver"
        discount_curve=None,       # function t -> DF(t)
    ):
        self.notional = notional
        self.strike = strike / 10000  # bps to decimal
        self.maturity = maturity
        self.cds_maturity = cds_maturity
        self.spread = spread / 10000  # bps to decimal
        self.volatility = volatility
        self.option_type = option_type.lower()
        self.discount_curve = self._to_interp(discount_curve)

    def price(self):
        if self.volatility <= 0 or self.spread <= 0:
            return 0.0

        T = self.maturity
        S = self.spread
        K = self.strike
        sigma = self.volatility
        df = self.discount_curve(T)

        d1 = (np.log(S / K) + 0.5 * sigma**2 * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)

        if self.option_type == "payer":
            price = df * (S * norm.cdf(d1) - K * norm.cdf(d2))
        elif self.option_type == "receiver":
            price = df * (K * norm.cdf(-d2) - S * norm.cdf(-d1))
        else:
            raise ValueError("option_type must be 'payer' or 'receiver'")

        # Convert to dollar value using risky annuity approximation
        risky_annuity = self._risky_annuity()
        return self.notional * price * risky_annuity

    def _to_interp(self, curve_input):
        if callable(curve_input):
            return curve_input
        else:
            times = sorted(curve_input.keys())
            values = [curve_input[t] for t in times]
            return interp1d(times, values, kind='linear', fill_value='extrapolate')

    def _risky_annuity(self):
        # Simplified risky annuity: PV of 1bp over CDS maturity
        # Approximation: sum of discounted flows annually
        steps = int(self.cds_maturity)
        annuity = sum(self.discount_curve(self.maturity + t) for t in range(1, steps + 1))
        return annuity
