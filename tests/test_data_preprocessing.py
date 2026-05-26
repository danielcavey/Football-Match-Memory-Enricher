from src.data_preprocessing import clean_columns_names

import pandas as pd

def test_clean_columns_names():
    df = pd.DataFrame(columns=[" Date ", "HOME TEAM", "Score "])
    out = clean_columns_names(df)
    assert list(out.columns) == ["date", "home team", "score"]