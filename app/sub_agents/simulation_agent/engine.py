import pandas as pd
import numpy as np
import os

CSV_PATH = os.path.join(
    os.getcwd(),
    "data",
    "datasets_uc4-market-activity-prediction-agent_30_yr_stock_market_data.csv"
)

SIM_COUNT = 10000

STRESS_REGIMES = {
    "calm": 0.7,
    "normal": 1.0,
    "stress": 1.8
}

TENOR_MAP = {
    "5Y": "Treasury Yield 5 Years (^FVX)",
    "10Y": "Treasury Yield 10 Years (^TNX)",
    "30Y": "Treasury Yield 30 Years (^TYX)"
}


def load_data():
    df = pd.read_csv(CSV_PATH)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    return df.dropna(subset=["Date"]).sort_values("Date")


def simulate_yield_changes(tenor: str, regime: str):
    df = load_data()
    series = pd.to_numeric(df[TENOR_MAP[tenor]], errors="coerce").dropna()

    yield_changes = series.diff().dropna()
    sigma = yield_changes.std() * STRESS_REGIMES[regime]

    return np.random.normal(0, sigma, SIM_COUNT)


def compute_metrics(simulated_changes):
    return {
        "VaR_95_YieldBps": round(np.percentile(simulated_changes, 5) * 10000, 2),
        "YieldRange_Bps": [
            round(simulated_changes.min() * 10000, 2),
            round(simulated_changes.max() * 10000, 2)
        ],
        "SimCount": SIM_COUNT
    }
