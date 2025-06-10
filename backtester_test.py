from strategy.backtester import Backtester
from pricers.cds_pricer import CDSPricer
from data.market_data import MarketDataProvider


def simple_cds_strategy(mkt_date, treasury_yields, cds_spreads):
    return {
        "notional": 10_000_000,
        "spread": cds_spreads.get(5, 200),  # bps
        "maturity": 5,
        "recovery_rate": 0.4
    }

md = MarketDataProvider()
# Load or simulate multiple days of market data
# md.set_market_data(...)

bt = Backtester(simple_cds_strategy, CDSPricer, md)
pnl_series = bt.run()
