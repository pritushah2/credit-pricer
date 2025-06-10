from pricers.cds_pricer import CDSPricer
from analytics.curve_construction import DiscountCurveBuilder, HazardCurveBuilder
from analytics.sensitivity import SensitivityEngine
from visualizations.risk_report_plot import plot_risk_report

# Create curves
dc = DiscountCurveBuilder([(1, 0.05), (3, 0.055), (5, 0.06)]).build_curve()
hc = HazardCurveBuilder([(1, 100), (3, 150), (5, 200)], dc).build_curve()

# Set up pricer
pricer = CDSPricer(
    notional=1e7,
    maturity=5,
    spread=150,
    recovery_rate=0.4,
    discount_curve=dc,
    hazard_rate_curve=hc
)

# Sensitivity analysis
engine = SensitivityEngine(pricer, dc, hc)
print("Parallel PV01s:", engine.compute_pv01())

# Key rate PV01s
kr_sens = engine.compute_key_rate_sensitivities(tenors=[1, 3, 5])
for tenor, sens in kr_sens.items():
    print(f"Tenor {tenor}y -> IR01: {sens['IR01']:.2f}, CS01: {sens['CS01']:.2f}")

cs01_by_tenor = {tenor: sens.get("CS01", 0) for tenor, sens in kr_sens.items()}
ir01_by_tenor = {tenor: sens.get("IR01", 0) for tenor, sens in kr_sens.items()}

plot_risk_report(
    cs01_by_tenor,
    ir01_by_tenor
)
