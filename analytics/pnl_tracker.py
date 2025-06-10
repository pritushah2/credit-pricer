# analytics/pnl_tracker.py

from copy import deepcopy
import numpy as np
from analytics.sensitivity import SensitivityEngine


class PnLTracker:
    def __init__(self, pricer, discount_curve_fn=None, hazard_curve_fn=None):
        self.pricer = deepcopy(pricer)
        self.base_dc = discount_curve_fn
        self.base_hc = hazard_curve_fn
        self.history = []

    def record_position(self, date, pricer):
        self.pricer = deepcopy(pricer)
        self.base_dc = pricer.discount_curve
        self.base_hc = pricer.hazard_rate_curve
        price = pricer.price()

        self.history.append({
            "date": date,
            "price": price,
            "daily_pnl": None,
            "pnl_attrib": None
        })

    def record_day(self, date, discount_curve_fn=None, hazard_curve_fn=None):
        """
        Records price and PnL attribution for a day.
        """
        # Use curves from the day or fallback to base
        dc = discount_curve_fn or self.base_dc
        hc = hazard_curve_fn or self.base_hc

        # Reprice instrument with new curves
        pricer_today = deepcopy(self.pricer)
        pricer_today.discount_curve = dc
        pricer_today.hazard_rate_curve = hc
        price_today = pricer_today.price()

        # If this is the first record, just save it
        if not self.history:
            self.history.append({
                "date": date,
                "price": price_today,
                "daily_pnl": None,
                "pnl_attrib": None
            })
            return

        # Previous state
        prev_record = self.history[-1]
        price_prev = prev_record["price"]

        # Compute sensitivities from previous day
        engine = SensitivityEngine(self.pricer, self.base_dc, self.base_hc)
        sens = engine.compute_pv01(bump_bp=1.0)

        # Compute IR and CS shifts
        ts = np.linspace(0.01, 30.0, 100)
        ir_shift = np.mean([dc(t) - self.base_dc(t) for t in ts])
        cs_shift = np.mean([hc(t) - self.base_hc(t) for t in ts])

        # PnL attribution via linear approximation
        ir01 = sens["IR01"]
        cs01 = sens["CS01"]
        pnl_ir = ir01 * (ir_shift * 10000)  # scale shift to bp
        pnl_cs = cs01 * (cs_shift * 10000)

        # Residual
        total_pnl = price_today - price_prev
        residual = total_pnl - pnl_ir - pnl_cs

        self.history.append({
            "date": date,
            "price": price_today,
            "daily_pnl": total_pnl,
            "pnl_attrib": {
                "IR_PnL": pnl_ir,
                "CS_PnL": pnl_cs,
                "Residual": residual
            }
        })

        # Update curves
        self.base_dc = dc
        self.base_hc = hc
        self.pricer = deepcopy(pricer_today)

    def compute_pnl_series(self):
        return self.history

    def last_price(self):
        return self.history[-1]["price"] if self.history else None
