import pandas as pd
from app.sub_agents.data_orchestrator.tools import get_yield_curve_data
from typing import Dict, Any
import numpy as np


def sanitize_for_json(obj: Any) -> Any:
    """
    Recursively convert objects to JSON-serializable Python types.

    Required for Google ADK + SSE because:
    - Pydantic cannot serialize numpy / pandas objects
    - SSE requires strict JSON compliance

    Handles:
    - numpy scalars (int64, float64, etc.)
    - pandas NA / NaT / Timestamp
    - DataFrames / Series
    - dicts / lists / tuples
    """

    # ---- Primitive safe types ----
    if obj is None:
        return None

    if isinstance(obj, (str, int, bool)):
        return obj

    if isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj

    # ---- numpy scalars ----
    if isinstance(obj, np.generic):
        return sanitize_for_json(obj.item())

    # ---- pandas types ----
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()

    if isinstance(obj, pd.Period):
        return str(obj)

    if isinstance(obj, pd.Timedelta):
        return obj.total_seconds()

    if pd.isna(obj):
        return None

    # ---- pandas containers ----
    if isinstance(obj, pd.DataFrame):
        df = obj.replace([np.nan, np.inf, -np.inf], None)
        return df.to_dict(orient="records")

    if isinstance(obj, pd.Series):
        return sanitize_for_json(obj.to_dict())

    # ---- collections ----
    if isinstance(obj, dict):
        return {str(k): sanitize_for_json(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple, set)):
        return [sanitize_for_json(v) for v in obj]

    # ---- fallback (last resort) ----
    try:
        return obj.__dict__
    except Exception:
        return str(obj)


def yield_curve_tool(horizon: str = "latest") -> Dict[str, Any]:
    """
    Fetch yield curve and macro data for prediction agents.

    Args:
        horizon:
            - "latest": most recent daily observation
            - "quarterly": most recent quarterly average
    """

    df = get_yield_curve_data()

    if horizon not in {"latest", "quarterly"}:
        return {
            "status": "error",
            "message": "Invalid horizon. Allowed values: latest, quarterly"
        }
    else:
        if df.empty:
            return {
                "status": "error",
                "message": "No yield curve data available"
            }

        # Ensure date column is datetime
        df["date"] = pd.to_datetime(df["date"])

        if horizon == "quarterly":
            # Aggregate to most recent quarter
            df["quarter"] = df["date"].dt.to_period("Q")
            latest_q = df["quarter"].max()
            df_q = df[df["quarter"] == latest_q]

            row = df_q.mean(numeric_only=True)
            policy_regime = df_q["regime"].mode().iloc[0]
            as_of = str(latest_q)

        else:
            # Latest daily observation
            df = df.sort_values("date", ascending=False)
            latest_row = df.iloc[0]

            row = latest_row
            policy_regime = latest_row["regime"]
            as_of = str(latest_row["date"].date())

        result = {
            "status": "success",
            "aggregation": horizon,
            "as_of": as_of,
            "policy_rate": float(row["fedfunds"]),
            "yields": {
                "5Y": float(row["y5"]),
                "10Y": float(row["y10"]),
                "30Y": float(row["y30"]),
            },
            "spreads": {
                "5s10s": float(row["y10"] - row["y5"]),
                "10s30s": float(row["y30"] - row["y10"]),
            },
            "macro": {
                "inflation": float(row["inflation_rate"]),
                "gdp_growth": float(row["gdp_growth"]),
                "unemployment": float(row["unemployment_rate"]),
            },
            "curve_volatility": float(row["curve_volatility"]),
            "policy_regime": policy_regime,
        }

        return sanitize_for_json(result)
        return result
