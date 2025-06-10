from typing import Callable, Dict, List
from datetime import date
from analytics.pnl_tracker import PnLTracker
from analytics.curve_construction import build_discount_curve_from_yields, build_hazard_curve_from_spreads
from copy import deepcopy

class Backtester:
    def __init__(self, pricer_class, market_data_provider, strategy_fn=None, fixed_kwargs=None):
        self.strategy_fn = strategy_fn
        self.fixed_kwargs = fixed_kwargs or {}
        self.pricer_class = pricer_class
        self.market_data = market_data_provider
        self.tracker = PnLTracker(pricer_class)
        self.positions = []


    def run(self):
        prev_pricer = None

        for i, dt in enumerate(self.market_data.available_dates()):
            # Get market data
            treasury_yields = self.market_data.get_treasury_yields(dt)
            cds_spreads = self.market_data.get_cds_spreads(dt)

            # Build market curves
            discount_curve_fn = build_discount_curve_from_yields(treasury_yields)
            hazard_curve_fn = build_hazard_curve_from_spreads(cds_spreads, discount_curve_fn)

            # Get strategy parameters
            if self.strategy_fn:
                instrument_kwargs = self.strategy_fn(dt, treasury_yields, cds_spreads)
            else:
                instrument_kwargs = self.fixed_kwargs

            if i == 0:
                # Only build and record pricer on first day
                pricer = self.pricer_class(discount_curve=discount_curve_fn,
                                        hazard_rate_curve=hazard_curve_fn,
                                        **instrument_kwargs)
                self.tracker = PnLTracker(pricer, discount_curve_fn, hazard_curve_fn)
                self.tracker.record_position(dt, pricer)
            else:
                # Reprice the same position using new market data
                self.tracker.record_day(dt, discount_curve_fn, hazard_curve_fn)

            # Save pricer per day if needed
            self.positions.append((dt, deepcopy(self.tracker.pricer)))

        return self.tracker.compute_pnl_series()