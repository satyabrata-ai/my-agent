import pandas as pd
from datetime import datetime

from app.sub_agents.data_orchestrator import tools as da_tools


def test_clean_price_dataframe_handles_missing_and_duplicates():
    today = datetime.utcnow().date()
    df = pd.DataFrame({
        "date": [today, today, None, today - pd.Timedelta(days=1)],
        "ticker": ["tst", "tst", "tst", "tst"],
        "close": [100.0, 101.0, 102.0, None]
    })

    cleaned = da_tools.clean_price_dataframe(df)
    # Should drop the None date and None close, remove duplicates and uppercase ticker
    assert cleaned['ticker'].iloc[0] == 'TST'
    assert cleaned['close'].min() >= 100.0
    assert cleaned['date'].isnull().sum() == 0
