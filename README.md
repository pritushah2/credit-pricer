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

credit-pricer/
│
├── credit_tools/ # Core modules
│ ├── cds_pricer.py # CDS pricing logic
│ ├── trs_pricer.py # TRS pricing logic
│ ├── discount_curve.py # Build and interpolate discount curves
│ ├── market_data.py # Market data handling
│ ├── scenario_analysis.py# Scenario simulation engine
│ └── init.py
│
├── data/ # Placeholder for yield/CDS data files
│
├── notebooks/ # Jupyter notebooks for testing and analysis
│
├── .gitignore # Ignored files and folders
└── README.md # You are here