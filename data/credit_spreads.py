import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from scipy.interpolate import interp1d


def fetch_treasury_yields():
    """
    Fetch U.S. Treasury yields from FRED via yfinance.
    Returns: DataFrame with maturities and yields
    """
    treasury_symbols = {
        "DGS1MO": 1/12,
        "DGS3MO": 0.25,
        "DGS6MO": 0.5,
        "DGS1": 1,
        "DGS2": 2,
        "DGS3": 3,
        "DGS5": 5,
        "DGS7": 7,
        "DGS10": 10,
        "DGS20": 20,
        "DGS30": 30
    }

    data = yf.download(list(treasury_symbols.keys()), period="5d", interval="1d")["Adj Close"]
    latest = data.dropna().iloc[-1]

    yields = pd.DataFrame({
        "Maturity": [treasury_symbols[sym] for sym in latest.index],
        "Treasury_Yield": latest.values / 100  # convert % to decimal
    })

    return yields.sort_values(by="Maturity").reset_index(drop=True)


def fetch_issuer_yields(issuer_ticker):
    """
    Fetch historical YTM-like proxy from issuer ETF or bond index (e.g., LQD, JPM, AAPL).
    Returns a flat curve for demo purposes.

    You can expand this later using FINRA TRACE or actual bond yields.
    """
    data = yf.download(issuer_ticker, period="5d", interval="1d")["Adj Close"]
    price = data.dropna().iloc[-1]

    # Simulated yield curve shape for issuer
    # Until we integrate real bond curve data, or direct CDS spreads, we need to make do with this
    simulated_curve = pd.DataFrame({
        "Maturity": [1, 3, 5, 7, 10],
        "Issuer_Yield": np.linspace(0.05, 0.06, 5)  # 5–6% flat-ish
    })

    return simulated_curve


def build_credit_spread_curve(issuer_curve, treasury_curve):
    """
    Align issuer and treasury maturities and compute credit spreads.
    Returns: DataFrame with Maturity, Treasury_Yield, Issuer_Yield, Spread
    """
    interp_treasury = interp1d(treasury_curve['Maturity'], treasury_curve['Treasury_Yield'], fill_value='extrapolate')
    issuer_curve['Treasury_Yield'] = issuer_curve['Maturity'].apply(interp_treasury)
    issuer_curve['Credit_Spread'] = issuer_curve['Issuer_Yield'] - issuer_curve['Treasury_Yield']

    return issuer_curve


def get_credit_spread_pipeline(issuer_ticker="LQD"):
    treasury = fetch_treasury_yields()
    issuer = fetch_issuer_yields(issuer_ticker)
    spread_df = build_credit_spread_curve(issuer, treasury)
    return spread_df
