import numpy as np
from datetime import timedelta, date

from strategy.backtester import Backtester
from pricers.cds_pricer import CDSPricer
from data.market_data import MarketDataProvider


def generate_simulated_market_data(num_days=20, start_date = None):
    if start_date is None:
        start_date = date.today()
    dates = [start_date - timedelta(days=i) for i in range(num_days)]

    simulated_data = []
    for d in dates:
        treasury_yields = {
            1: 0.05 + np.random.normal(0, 0.002),
            3: 0.055 + np.random.normal(0, 0.002),
            5: 0.06 + np.random.normal(0, 0.002),
            10: 0.065 + np.random.normal(0, 0.002),
        }
        cds_spreads = {
            1: 100 + np.random.normal(0, 5),
            3: 150 + np.random.normal(0, 5),
            5: 200 + np.random.normal(0, 5),
        }
        simulated_data.append((d, treasury_yields, cds_spreads))

    return simulated_data


def simple_cds_strategy(mkt_date, treasury_yields, cds_spreads):
    return {
        "notional": 10_000_000,
        "spread": cds_spreads.get(5, 200),  # fallback default
        "maturity": 5,
        "recovery_rate": 0.4
    }


def run_simulated_backtest():
    md = MarketDataProvider()
    simulated_data = generate_simulated_market_data(20)
    md.set_market_data(simulated_data)

    bt = Backtester(simple_cds_strategy, CDSPricer, md)
    pnl_series = bt.run()
    return pnl_series

from datetime import timedelta

def run_ui_backtest(pricer_class, market_data_provider, strategy_fn=None, fixed_kwargs=None, 
                           start_date=None, days=20):
    # Generate simulated market data for 'days' starting from start_date or today
    
    simulated_data = generate_simulated_market_data(20)

    # Load simulated data into market data provider
    for (market_date, treasury_yields, cds_spreads) in simulated_data:
        market_data_provider.set_market_data(market_date, treasury_yields, cds_spreads)

    # Initialize backtester with given params
    bt = Backtester(pricer_class=pricer_class,
                    market_data_provider=market_data_provider,
                    strategy_fn=strategy_fn,
                    fixed_kwargs=fixed_kwargs)

    # Run the backtest and get pnl series
    pnl_series = bt.run()

    return pnl_series