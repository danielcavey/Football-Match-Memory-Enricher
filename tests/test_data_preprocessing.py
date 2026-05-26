from src.data_preprocessing import clean_columns_names

import pandas as pd

def test_clean_columns_names():
    df = pd.DataFrame(columns=[" Date ", "HOME TEAM", "Score "])
    out = clean_columns_names(df)
    assert list(out.columns) == ["date", "home team", "score"]

def test_add_match_id():
    df = pd.DataFrame({"games": ["A vs B", "C vs D"]})
    out = add_match_id(df)
    assert list(out["match_id"]) == [1, 2]