import pandas as pd
from datetime import datetime, timedelta

from app.sub_agents.data_orchestrator import tools as da_tools


def make_price_series(days: int = 10, start_price: float = 100.0):
    today = datetime.utcnow().date()
    dates = [today - timedelta(days=x) for x in reversed(range(days))]
    prices = [start_price * (1 + 0.01 * (i - days//2)/days) for i in range(days)]
    df = pd.DataFrame({"date": dates, "ticker": ["EVT"]*days, "close": prices})
    return df


def make_event_df(dates):
    df = pd.DataFrame({"date": dates, "ticker": ["EVT"]*len(dates), "event_type": ["Earnings"]*len(dates)})
    return df


def test_compute_event_impact(monkeypatch):
    price_df = make_price_series(30, 100.0)
    # create events in middle
    today = datetime.utcnow().date()
    event_dates = [today - timedelta(days=10), today - timedelta(days=5)]
    event_df = make_event_df(event_dates)

    # patch query_to_df to return events first then prices
    def fake_query(sql, limit=None):
        if 'event_calendar' in sql or 'events' in sql:
            return event_df
        return price_df

    monkeypatch.setattr(da_tools._bq_store, "query_to_df", fake_query)

    res = da_tools.compute_event_impact("EVT", "Earnings", pre_window_days=1, post_window_days=1)
    assert res["status"] == "success"
    assert res["count"] >= 1
    assert "average_move" in res
