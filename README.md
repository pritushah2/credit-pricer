# Credit Pricer Toolkit 🏦📉

A Python-based toolkit for pricing and analyzing credit products including:

- **Credit Default Swaps (CDS)**
- **Index CDS**
- **Total Return Swaps (TRS)**
- **Scenario Analysis for Credit Instruments**

Built for use in credit strategy roles at hedge funds, trading desks, or risk teams.

---

## 🔧 Features

- 📈 **CDS Pricing Engine**  
  Compute fair CDS spreads using survival curves and discounting.

- 🧮 **TRS Cashflow Simulation**  
  Simulate total return and floating leg cashflows under various scenarios.

- 💹 **Market Data Integration**  
  Pull and utilize historical or mock market data for rates and spreads.

- 🔬 **Scenario Analysis**  
  Perform time-based or market-shock simulations to evaluate portfolio impact.

---

## 📁 Project Structure

credit_toolkit/
│
├── pricers/
│   ├── cds_pricer.py
│   ├── index_cds_pricer.py
│   ├── trs_pricer.py
│   └── credit_option_pricer.py
│
├── analytics/
│   ├── curve_construction.py
│   ├── scenario_analysis.py
│   ├── sensitivity.py
│   └── pnl_tracker.py
│
├── data/
│   └── market_data.py
│
├── strategy/
│   └── backtester.py
│
├── visualizations/
│   ├── risk_report_plot.py
│   └── pnl_plot.py
│
├── app.py   # Front CLI or Streamlit dashboard
└── README.md # You are here