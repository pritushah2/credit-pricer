import numpy as np
import datetime
from pandas_datareader.data import DataReader
from scipy.interpolate import interp1d
from scipy.optimize import minimize_scalar
from scipy.interpolate import CubicSpline

class DiscountCurveBuilder:
    def __init__(self, instruments = []):
        """
        instruments: list of tuples (tenor in years, rate)
        e.g., [(0.25, 0.03), (0.5, 0.032), (1.0, 0.035), (2.0, 0.037)]
        """
        self.instruments = sorted(instruments)
    
    def fetch_discount_curve(self):
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
                data.append({time, discount})
            except Exception as e:
                print(f"Warning: Could not fetch {label}: {e}")

        return data

    def build_curve(self):
        dfs = {}
        self.instruments = self.instruments if self.instruments else self.fetch_discount_curve()

        for t, r in self.instruments:
            df = 1 / (1 + r * t)  # simple discount factor from zero rate
            dfs[t] = df
        return interp1d(list(dfs.keys()), list(dfs.values()), kind='linear', fill_value='extrapolate')


class HazardCurveBuilder:
    def __init__(self, cds_spreads, discount_curve, recovery_rate=0.4):
        """
        cds_spreads: list of tuples (tenor in years, spread in bps)
        discount_curve: callable discount curve (e.g., from DiscountCurveBuilder)
        recovery_rate: assumed recovery
        """
        self.cds_spreads = sorted(cds_spreads)
        self.discount_curve = discount_curve
        self.recovery_rate = recovery_rate

    def _cds_pv(self, hazard_rate, maturity, spread):
        """
        Calculate PV of CDS with flat hazard rate (used for bootstrapping).
        """
        times = np.linspace(0, maturity, 100)
        survival_probs = np.exp(-hazard_rate * times)
        dt = maturity / 100

        # Premium leg
        premium = 0
        for t in np.arange(0.25, maturity + 0.01, 0.25):
            df = self.discount_curve(t)
            sp = np.exp(-hazard_rate * t)
            premium += df * sp * 0.25
        premium *= spread / 10000

        # Protection leg
        prot = 0
        for i in range(1, len(times)):
            t0, t1 = times[i - 1], times[i]
            sp0, sp1 = survival_probs[i - 1], survival_probs[i]
            default_prob = sp0 - sp1
            df = self.discount_curve((t0 + t1) / 2)
            prot += df * default_prob
        prot *= (1 - self.recovery_rate)

        return prot - premium

    def build_curve(self):
        hazard_curve = {}
        last_rate = 0.01  # Starting guess

        for tenor, spread in self.cds_spreads:
            def objective(h):
                return abs(self._cds_pv(h, tenor, spread))

            res = minimize_scalar(objective, bounds=(0.0001, 0.5), method='bounded')
            last_rate = res.x
            hazard_curve[tenor] = last_rate

        return interp1d(list(hazard_curve.keys()), list(hazard_curve.values()), kind='linear', fill_value='extrapolate')

def build_discount_curve_from_yields(yield_curve: dict):
    """
    Build a discount factor curve from Treasury yields.

    Parameters:
        yield_curve (dict): {tenor_years: yield (as decimal)}
            Example: {1: 0.05, 2: 0.052, 5: 0.055}

    Returns:
        Callable: function t -> DF(t), using linear interpolation
    """
    tenors = np.array(sorted(yield_curve.keys()))
    yields = np.array([yield_curve[t] for t in tenors])

    # Convert yields to discount factors: DF(t) = exp(-y * t)
    discounts = np.exp(-yields * tenors)

    return interp1d(tenors, discounts, kind="linear", fill_value="extrapolate")



def build_hazard_curve_from_spreads(spread_curve: dict, discount_curve: callable, recovery_rate: float = 0.4):
    """
    Build a hazard rate curve by bootstrapping from CDS spreads.

    Parameters:
        spread_curve (dict): {tenor_years: spread in bps}
        discount_curve (Callable): function t -> discount factor
        recovery_rate (float): assumed recovery rate

    Returns:
        Callable: hazard_rate(t)
    """
    def cds_pv(hazard_rate, maturity, spread):
        times = np.linspace(0, maturity, 100)
        survival_probs = np.exp(-hazard_rate * times)
        dt = maturity / 100

        # Premium leg
        premium_leg = 0
        for t in np.arange(0.25, maturity + 0.01, 0.25):
            df = discount_curve(t)
            sp = np.exp(-hazard_rate * t)
            premium_leg += df * sp * 0.25
        premium_leg *= spread / 10_000

        # Protection leg
        protection_leg = 0
        for i in range(1, len(times)):
            t0, t1 = times[i - 1], times[i]
            sp0, sp1 = survival_probs[i - 1], survival_probs[i]
            default_prob = sp0 - sp1
            df = discount_curve((t0 + t1) / 2)
            protection_leg += df * default_prob
        protection_leg *= (1 - recovery_rate)

        return protection_leg - premium_leg

    hazard_curve = {}
    for tenor in sorted(spread_curve.keys()):
        spread = spread_curve[tenor]

        result = minimize_scalar(
            lambda h: abs(cds_pv(h, tenor, spread)),
            bounds=(0.0001, 0.5),
            method="bounded"
        )
        hazard_curve[tenor] = result.x

    return interp1d(
        list(hazard_curve.keys()),
        list(hazard_curve.values()),
        kind="linear",
        fill_value="extrapolate"
    )