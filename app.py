import streamlit as st
import numpy as np
import pandas as pd
from datetime import date

from pricers.cds_pricer import CDSPricer
from pricers.index_cds_pricer import IndexCDSPricer
from pricers.trs_pricer import TRSPricer
from pricers.credit_option_pricer import CreditOptionPricer
from analytics.curve_construction import build_discount_curve_from_yields, build_hazard_curve_from_spreads
from visualizations.pnl_plot import plot_pnl_series
from visualizations.risk_report_plot import plot_risk_report
from analytics.sensitivity import SensitivityEngine
from strategy.sim_backtest import run_ui_backtest
from data.market_data import MarketDataProvider

st.set_page_config(page_title="Credit Toolkit Dashboard", layout="wide")
st.title("Credit Pricing & Risk Dashboard")

instrument = st.sidebar.selectbox("Choose Instrument", ["CDS", "Index CDS", "TRS", "Credit Option"])

# --- Common Inputs ---
notional = st.sidebar.number_input("Notional", 1_000_000, 100_000_000, 10_000_000, step=1_000_000)
maturity = st.sidebar.slider("Maturity (Years)", 1, 10, 5)

# --- Market Curves ---
st.sidebar.markdown("### Treasury Yields")
treasury_yields = {
    int(k): float(st.sidebar.number_input(f"Yield {k}Y", value=rate))
    for k, rate in {1: 0.05, 3: 0.055, 5: 0.06, 10: 0.065}.items()
}
discount_curve = build_discount_curve_from_yields(treasury_yields)

st.sidebar.markdown("### CDS Spreads (bps)")
cds_spreads = {
    int(k): float(st.sidebar.number_input(f"Spread {k}Y", value=spread))
    for k, spread in {1: 100, 3: 150, 5: 200}.items()
}
hazard_curve = build_hazard_curve_from_spreads(cds_spreads, discount_curve)

print("discount_curve type:", type(discount_curve))
print("hazard_curve type:", type(hazard_curve))

# --- Instrument-specific Inputs ---
if instrument == "CDS":
    spread = st.number_input("CDS Spread (bps)", 50, 1000, 200)
    pricer = CDSPricer(notional, maturity, spread, 0.4, discount_curve, hazard_curve)

elif instrument == "Index CDS":
    spread = st.number_input("Index Spread (bps)", 50, 1000, 250)
    num_names = st.number_input("Number of Names", 50, 150, 125)
    defaulted_names = st.number_input("Defaulted Names", 0, 125, 0)
    pricer = IndexCDSPricer(notional, maturity, spread, 0.4, discount_curve, hazard_curve, num_names, defaulted_names)

elif instrument == "TRS":
    coupon_rate = st.number_input("Coupon Rate", 0, 10, 3)
    spread = st.number_input("Funding Spread (bps)", 0, 500, 150)
    pricer = TRSPricer(notional, maturity, spread, coupon_rate, 0.4, discount_curve, hazard_curve)

elif instrument == "Credit Option":
    cds_maturity = st.number_input("Underlying CDS Maturity", 1, 10, 3)
    strike = st.number_input("Strike Spread (bps)", 100, 500, 180)
    spread = st.number_input("Forward Spread (bps)", 100, 500, 200)
    volatility = st.number_input("Volatility (decimal)", 0.05, 1.0, 0.3)
    option_type = st.selectbox("Option Type", ["payer", "receiver"])
    pricer = CreditOptionPricer(notional, strike, maturity, cds_maturity, spread, volatility, option_type, discount_curve)

# --- Results ---
st.subheader(f"{instrument} Price")
st.success(f"💰 Price: ${pricer.price():,.2f}")

# --- Optional Plots ---
st.markdown("Show Risk Report")
if st.button("Generate Risk Report"):
    with st.spinner("Computing Sensitivities..."):
        
        engine = SensitivityEngine(pricer, discount_curve, hazard_curve)

        # 1. Key rate PV01s
        sensitivities = engine.compute_key_rate_sensitivities(tenors=[1, 3, 5])

        # 2. Extract CS01 and IR01 into separate dicts
        cs01_by_tenor = {tenor: sens.get("CS01", 0) for tenor, sens in sensitivities.items()}
        ir01_by_tenor = {tenor: sens.get("IR01", 0) for tenor, sens in sensitivities.items()}

        # 3. Plot
        fig = plot_risk_report(cs01_by_tenor, ir01_by_tenor)
        st.pyplot(fig)

if st.checkbox("Show Simulated PnL Series"):
    days = 10
    base_spread = spread
    spread_series = base_spread + np.random.normal(0, 5, days)

    pnl_series = []
    prev_price = None

    for i, s in enumerate(spread_series):
        # Reprice based on instrument type and simulated spread
        if instrument == "CDS":
            pricer = CDSPricer(notional, maturity, s, 0.4, discount_curve, hazard_curve)
            price = pricer.price()

        elif instrument == "Index CDS":
            pricer = IndexCDSPricer(notional, maturity, s, 0.4, discount_curve, hazard_curve, num_names, defaulted_names)
            price = pricer.price()

        elif instrument == "TRS":
            pricer = TRSPricer(notional, maturity, s, coupon_rate, 0.4, discount_curve, hazard_curve)
            price = pricer.price()

        elif instrument == "Credit Option":
            pricer = CreditOptionPricer(notional, strike, maturity, cds_maturity, s, volatility, option_type, discount_curve)
            price = pricer.price()

        # Compute PnL as price change
        daily_pnl = None if prev_price is None else price - prev_price
        pnl_series.append({
            "date": pd.Timestamp.today() + pd.Timedelta(days=i),
            "daily_pnl": daily_pnl,
            "price": price
        })
        prev_price = price

    fig = plot_pnl_series(pnl_series)
    st.pyplot(fig)

# if st.checkbox("Run Backtest Simulation"):
#     # Prepare config from UI
#     md = MarketDataProvider()
#     base_config = {
#         "notional": notional,
#         "maturity": maturity,
#         "recovery_rate": 0.4,
#     }

#     if instrument == "CDS":
#         pricer_cls = CDSPricer
#         base_config["spread"] = spread
#     elif instrument == "Index CDS":
#         pricer_cls = IndexCDSPricer
#         base_config["num_names"] = num_names
#         base_config["defaulted_names"] = defaulted_names
#     elif instrument == "TRS":
#         pricer_cls = TRSPricer
#         base_config["coupon_rate"] = coupon_rate
#         base_config["spread"] = spread
#     elif instrument == "Credit Option":
#         pricer_cls = CreditOptionPricer
#         base_config.update({
#             "strike": strike,
#             "volatility": volatility,
#             "option_type": option_type,
#             "cds_maturity": cds_maturity,
#             "spread": spread
#         })

#     pnl_series = run_ui_backtest(pricer_cls, md, None, base_config)
#     fig = plot_pnl_series(pnl_series)
#     st.pyplot(fig)