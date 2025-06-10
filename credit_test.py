from pricers.cds_pricer import CDSPricer
from pricers.index_cds_pricer import IndexCDSPricer
from pricers.trs_pricer import TRSPricer
from analytics.curve_construction import DiscountCurveBuilder, HazardCurveBuilder
from pricers.credit_option_pricer import CreditOptionPricer

# Input market instruments
# deposit_rates = [(0.25, 0.03), (0.5, 0.031), (1.0, 0.033), (2.0, 0.035)]
cds_spreads = [(1.0, 100), (3.0, 150), (5.0, 200)]

# Build discount curve
dc_builder = DiscountCurveBuilder()
discount_curve = dc_builder.build_curve()

# Build hazard rate curve
hc_builder = HazardCurveBuilder(cds_spreads, discount_curve, recovery_rate=0.4)
hazard_curve = hc_builder.build_curve()

# Use the curve at arbitrary points
print("Discount factor at 1.5y:", discount_curve(1.5))
print("Hazard rate at 2y:", hazard_curve(2.0))

pricer = TRSPricer(
    notional=1e7,
    maturity=5.0,
    spread=100,  # TRS spread 100 bps
    coupon_rate=0.05,  # 5% bond coupon
    recovery_rate=0.4,
    discount_curve=discount_curve,
    hazard_rate_curve=hazard_curve,
    financing_rate=0.03  # 3% cost of funds
)
price = pricer.price()
print(f"TRS price: {price:,.2f}")

pricer = IndexCDSPricer(
    notional=1e7,
    maturity=5.0,
    index_spread=60,  # 60 bps
    recovery_rate=0.4,
    discount_curve=discount_curve,
    hazard_rate_curve=hazard_curve,
    num_names=125,
    defaults=3
)
price = pricer.price()
print(f"Index CDS price: {price:,.2f}")

pricer = CDSPricer(
    notional=1e7,
    maturity=5.0,
    spread=100,  # 100 bps = 1%
    recovery_rate=0.4,
    discount_curve=discount_curve,
    hazard_rate_curve=hazard_curve
)

price = pricer.price()
print(f"CDS price: {price:,.2f}")

pricer = CreditOptionPricer(
    notional=1e7,
    strike=180,
    maturity=1.0,
    cds_maturity=5.0,
    spread=200,  # current forward CDS spread
    volatility=0.3,
    option_type="payer",
    discount_curve=discount_curve
)

print("CDS Option Price: ", round(pricer.price(), 2))
