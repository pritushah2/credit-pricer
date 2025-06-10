import os
import datetime
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline
from pandas_datareader.data import DataReader

# Configuration
DIR_PATH = "data_store/discount_curve"

def fetch_discount_curve():
    os.makedirs(DIR_PATH, exist_ok=True)
    date_str = datetime.datetime.today().strftime("%Y-%m-%d")
    path = os.path.join(DIR_PATH, f"{date_str}.csv")

    if os.path.exists(path):
        df = pd.read_csv(path)
        return df

    # Treasury yield FRED codes
    tickers = {
        '1M': 'DGS1MO',
        '3M': 'DGS3MO',
        '6M': 'DGS6MO',
        '1Y': 'DGS1',
        '2Y': 'DGS2',
        '3Y': 'DGS3',
        '5Y': 'DGS5',
        '7Y': 'DGS7',
        '10Y': 'DGS10',
        '20Y': 'DGS20',
        '30Y': 'DGS30'
    }

    tenor_years = {
        '1M': 1 / 12,
        '3M': 0.25,
        '6M': 0.5,
        '1Y': 1,
        '2Y': 2,
        '3Y': 3,
        '5Y': 5,
        '7Y': 7,
        '10Y': 10,
        '20Y': 20,
        '30Y': 30
    }

    # Fetch latest yield data
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=7)

    data = []
    for label, fred_code in tickers.items():
        try:
            df = DataReader(fred_code, 'fred', start, end)
            rate = df.ffill().iloc[-1, 0] / 100  # Convert to decimal
            time = tenor_years[label]
            discount = np.exp(-rate * time)
            data.append({'time': time, 'discount_factor': discount})
        except Exception as e:
            print(f"Warning: Could not fetch {label}: {e}")

    df_curve = pd.DataFrame(data).sort_values('time')

    df_curve.to_csv(path, index=False)
    return data

