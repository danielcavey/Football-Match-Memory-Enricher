from src.data_preprocessing import (
    clean_columns_names, 
    add_match_id, 
    forward_fill,
    split_teams,
    split_scores,
    group_matches
)

import pandas as pd

def test_clean_columns_names():
    df = pd.DataFrame(columns=[" Date ", "HOME TEAM", "Score "])
    output = clean_columns_names(df)
    assert list(output.columns) == ["date", "home team", "score"]

def test_add_match_id():
    df = pd.DataFrame({"games": ["A vs B", "C vs D"]})
    output = add_match_id(df)
    assert list(output["match_id"]) == [1, 2]

def forward_fill(df):
    #ffill() replaces NULL values with the values from the previous row
    df[['date', 'games', 'ground', 'score']] = df[['date', 'games', 'ground', 'score']].ffill()
    return df

def test_forward_fill():
    df = pd.DataFrame({
        "match_id": [1, 1, 2],
        "date": ["2024", "2024", "2025"],
        "games": ["Arsenal versus Brentford", None, "Chelsea versus Darlington"],
        "ground": ["Emirates Stadium", None, "Gtech Community Stadium"],
        "score": ["2-1", None, "1-0"],
        "goalscorer(s)": ["Olivier Giroud", "Aaron Ramsey", "Ivan Toney"]
    })    
    output = forward_fill(df)
    assert len(output) == 3
    assert output["ground"].iloc[1] == "Emirates Stadium"
    assert output["score"].iloc[1] == "2-1"

def test_split_teams():
    df = pd.DataFrame({"games": ["Arsenal versus Brentford"]})
    output = split_teams(df)
    assert output["home team"].iloc[0] == "Arsenal"
    assert output["away team"].iloc[0] == "Brentford"

def test_split_scores():
    df = pd.DataFrame({"score": ["2-1"]})
    output = split_scores(df)
    assert output["home score"].iloc[0] == "2"
    assert output["away score"].iloc[0] == "1"

def test_group_matches():
    df = pd.DataFrame({
        "match_id": [1, 1, 2],
        "date": ["2024", "2024", "2025"],
        "ground": ["Emirates Stadium", "Emirates Stadium", "Gtech Community Stadium"],
        "home team": ["Arsenal", "Arsenal", "Brentford"],
        "home score": ["2", "2", "1"],
        "away team": ["Chelsea", "Chelsea", "Darlington"],
        "away score": ["0", "0", "0"],
        "goalscorer(s)": ["Olivier Giroud", "Aaron Ramsey", "Ivan Toney"]
    })
    output = group_matches(df)
    assert len(output) == 2
    assert output["ground"].iloc[0] == "Emirates Stadium"
    assert output["goalscorer(s)"].iloc[0] == ["Olivier Giroud", "Aaron Ramsey"]
    assert output["goalscorer(s)"].iloc[1] == ["Ivan Toney"]