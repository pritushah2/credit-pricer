# data/market_data.py

from datetime import date
from typing import Dict


class MarketDataProvider:
    def __init__(self):
        # You could load from files, APIs, or simulate in real app
        self.curves_by_date = {}

    def set_market_data(self, market_date: date,
                        treasury_yields: Dict[int, float],
                        cds_spreads: Dict[int, float]):
        """
        Set market data for a given date.

        Parameters:
        - treasury_yields: {tenor_years: yield in decimal}
        - cds_spreads: {tenor_years: spread in bps}
        """
        self.curves_by_date[market_date] = {
            "treasury_yields": treasury_yields,
            "cds_spreads": cds_spreads
        }

    def get_treasury_yields(self, market_date: date) -> Dict[int, float]:
        return self.curves_by_date[market_date]["treasury_yields"]

    def get_cds_spreads(self, market_date: date) -> Dict[int, float]:
        return self.curves_by_date[market_date]["cds_spreads"]

    def available_dates(self):
        return sorted(self.curves_by_date.keys())
