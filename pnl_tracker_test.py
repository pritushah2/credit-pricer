from datetime import date
from pricers.cds_pricer import CDSPricer
from analytics.curve_construction import DiscountCurveBuilder, HazardCurveBuilder
from analytics.pnl_tracker import PnLTracker
from visualizations.pnl_plot import plot_pnl_series

# Setup day 1 market
dc1 = DiscountCurveBuilder([(1, 0.05), (3, 0.055), (5, 0.06)]).build_curve()
hc1 = HazardCurveBuilder([(1, 100), (3, 150), (5, 200)], dc1).build_curve()

# Setup day 2 market (interest rates down, spreads wider)
dc2 = DiscountCurveBuilder([(1, 0.048), (3, 0.053), (5, 0.058)]).build_curve()
hc2 = HazardCurveBuilder([(1, 110), (3, 160), (5, 210)], dc2).build_curve()

# Setup pricer
pricer = CDSPricer(
    notional=1e7,
    maturity=5,
    spread=150,
    recovery_rate=0.4,
    discount_curve=dc1,
    hazard_rate_curve=hc1
)

tracker = PnLTracker(pricer, dc1, hc1)

tracker.record_day(date(2025, 5, 26))         # Base day
tracker.record_day(date(2025, 5, 27), dc2, hc2)  # Market moves

for row in tracker.compute_pnl_series():
    print(row)

pnl_data = tracker.compute_pnl_series()
plot_pnl_series(pnl_data, show_attribution=True)