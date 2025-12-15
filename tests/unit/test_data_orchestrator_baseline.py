import pandas as pd
from datetime import datetime, timedelta

from app.sub_agents.data_orchestrator import tools as da_tools


def make_sample_price_df(days: int = 40, start_price: float = 100.0):
    today = datetime.utcnow().date()
    dates = [today - timedelta(days=x) for x in reversed(range(days))]
    prices = []
    p = start_price
    for i in range(days):
        p = p * (1 + (0.001 if i % 2 == 0 else -0.001))
        prices.append(round(p, 4))

    df = pd.DataFrame({
        "date": dates,
        "ticker": ["TEST"] * days,
        "close": prices,
    })
    return df


def test_get_baseline_metrics_computes_vol_and_ma(monkeypatch):
    df = make_sample_price_df(60, 100.0)

    # Monkeypatch the BQ store to return our sample dataframe
    monkeypatch.setattr(da_tools, "_bq_store", da_tools._bq_store)

    def fake_query(sql, limit=None):
        return df

    monkeypatch.setattr(da_tools._bq_store, "query_to_df", fake_query)

    res = da_tools.get_baseline_metrics("TEST")
    assert res["status"] == "success"
    result = res["result"]
    assert result["Ticker"] == "TEST"
    assert "HistVol_5D_Ann" in result
    assert result["MA_5"] is not None
    assert result["MA_20"] is not None
