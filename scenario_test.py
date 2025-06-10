from pricers.cds_pricer import CDSPricer
from analytics.curve_construction import DiscountCurveBuilder, HazardCurveBuilder
from analytics.scenario_analysis import ScenarioEngine

# Build base curves
dc = DiscountCurveBuilder([(1, 0.05), (3, 0.055), (5, 0.06)]).build_curve()
hc = HazardCurveBuilder([(1, 100), (3, 150), (5, 200)], dc).build_curve()

# Base pricer
pricer = CDSPricer(
    notional=1e7,
    maturity=5,
    spread=150,
    recovery_rate=0.4,
    discount_curve=dc,
    hazard_rate_curve=hc
)

# Scenario Engine
engine = ScenarioEngine(pricer, dc, hc)
engine.run_scenario("base")
engine.run_scenario("parallel_rate_up", dc_shift=0.01)
engine.run_scenario("credit_deterioration", hc_shift=0.01)
engine.run_scenario("steepening", dc_key_rate_shifts={1: 0.002, 5: 0.01})

# Print results
for scenario, data in engine.summarize().items():
    print(f"{scenario}: Price = {data['price']:.2f}, Δ = {data['delta']:.2f}")
