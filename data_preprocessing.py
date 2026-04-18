import pandas as pd

# Read in dataset
df = pd.read_excel("Live Football matches record raw.xlsx")

# Preprocessing

# Adjust column names to have no white space and no capitals
# strip() removes whitespace
# Avoids abiguity and potential for bugs
df.columns = [col.strip().lower() for col in df.columns]

# Give each match a unique ID
# Make match ID the first column
df['match_id'] = (df['games'].notna()).cumsum()
df = df[['match_id'] + [col for col in df.columns if col != 'match_id']]

#ffill() replaces NULL values with the values from the previous row
df[['date', 'games', 'ground', 'score']] = df[['date', 'games', 'ground', 'score']].ffill()

# Create a column listing the home team and a column listing the away team
# Drop the original game column
teams = df["games"].str.split("versus", expand=True)
df["home team"] = teams[0].str.strip()
df["away team"] = teams[1].str.strip()
df = df.drop('games', axis=1)

# Create a column listing the home score and a column listing the away score
# Drop the original score column
scores = df["score"].str.split("-", expand = True)
df["home score"] = scores[0].str.strip()
df["away score"] = scores[1].str.strip()
df = df.drop('score', axis=1)

# Group all rows according to match using match_id
# Almost all features default to the first instance of the match_id. This is okay since they are the same
# Exception is the goalscorers which are concatenated into a list
# Order of the columns is determined by the way they are listed here
grouped = df.groupby('match_id')
clean_df = grouped.agg({
    'date': 'first',
    'ground': 'first',
    'home team': 'first',
    'home score': 'first',
    'away team': 'first',
    'away score': 'first',
    'goalscorer(s)': lambda x: list(x.dropna())
})

# Save the new cleaned dataset into a new file
clean_df.to_csv("clean_matches.csv", index=False)