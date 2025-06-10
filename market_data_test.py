from data.market_data import MarketDataProvider
from datetime import date

md = MarketDataProvider()

md.set_market_data(
    date(2025, 5, 26),
    treasury_yields={1: 0.05, 3: 0.055, 5: 0.06, 10: 0.065},
    cds_spreads={1: 100, 3: 150, 5: 200}
)

# Fetch market data
yields = md.get_treasury_yields(date(2025, 5, 26))
spreads = md.get_cds_spreads(date(2025, 5, 26))
print("Treasury Yields:", yields)
print("CDS Spreads:", spreads)
