# Import dependencies
# Standard python libraries
import os
# Third-party libraries
from flask import Flask, redirect, request, url_for, render_template, session
import pandas as pd
# Internal imports
from db import get_df
from mfl import get_mfl_league, get_mfl_liveScoring, get_mfl_projectedScores

# Find environment variables
DATABASE_URL = os.environ.get("DATABASE_URL", None)
# sqlalchemy deprecated urls which begin with "postgres://"; now it needs to start with "postgresql://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

user_league = "53906"
week = "2"

# Create a new Flask instance
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# Create Flask route
@app.route('/')
def index():
    matchNumber = 0
    # Get required data
    leagueDF = get_mfl_league(user_league)
    liveDF = get_mfl_liveScoring(user_league)
    projDF = get_mfl_projectedScores(user_league, week)
    players = get_df("player_df")
    players = players.rename(columns={"PlayerID":"id_mfl"})
    # Merge datasets
    df = players.merge(
        projDF, on="id_mfl", how="left"
    ).merge(
        liveDF, on="id_mfl", how="left"
    ).merge(
        leagueDF, on="franchiseID", how="left"
    )
    # Reorder columns
    df = df[["matchup", "franchiseName", "status", "Name", "Position", "Team", "sharkProjection", "liveScore", "secondsRemaining"]]
    # Clean df
    df.dropna(inplace=True)
    # Define data types
    df['sharkProjection'] = df['sharkProjection'].astype('float32', copy=False)
    df['liveScore'] = df['liveScore'].astype('float32', copy=False)
    df['secondsRemaining'] = df['secondsRemaining'].astype('int', copy=False)
    df['matchup'] = df['matchup'].astype('int', copy=False)
    # Calculate final Projections based on amount of time remaining
    def calcScore(row):
        # Use a different calculation method for defenses since defenses do not accrue points
        if row["Position"] != "DF":
            result = row['liveScore'] + (row['sharkProjection'] * row['secondsRemaining'] / 3600)
        else:
            result = (row['sharkProjection'] * row['secondsRemaining'] + row['liveScore'] * (3600 - row['secondsRemaining'])) / 3600
        return result
    df['finalProjection'] = df.apply(calcScore, axis=1)
    # Create matchup summary table
    starts = df.loc[df['status']=="starter"]
    matchSumm = starts.groupby(['matchup',"franchiseName"])['finalProjection'].sum()
    matchSumm = pd.DataFrame(matchSumm)
    matchSumm = matchSumm.reset_index()
    matchSumm.loc[matchSumm.index%2==0, 'pivotIndex'] = "A" 
    matchSumm.loc[matchSumm.index%2==1, 'pivotIndex'] = "B"
    matchSumm = matchSumm[['matchup', 'pivotIndex', 'franchiseName', 'finalProjection']]
    matchSumm = matchSumm.reset_index(drop=True)
    # Collect matchup summaries for header table
    M1A = matchSumm.loc[matchSumm.matchup==0].drop(columns=['matchup', 'pivotIndex'])
    M2A = matchSumm.loc[matchSumm.matchup==1].drop(columns=['matchup', 'pivotIndex'])
    M3A = matchSumm.loc[matchSumm.matchup==2].drop(columns=['matchup', 'pivotIndex'])
    M4A = matchSumm.loc[matchSumm.matchup==3].drop(columns=['matchup', 'pivotIndex'])
    M5A = matchSumm.loc[matchSumm.matchup==4].drop(columns=['matchup', 'pivotIndex'])
    M6A = matchSumm.loc[matchSumm.matchup==5].drop(columns=['matchup', 'pivotIndex'])
    #Get franchise Names based on which matchup is selected
    franchiseA = matchSumm.loc[(matchSumm.matchup==0) & (matchSumm.pivotIndex=="A"), 'franchiseName'][matchNumber]
    franchiseB = matchSumm.loc[(matchSumm.matchup==0) & (matchSumm.pivotIndex=="B"), 'franchiseName'][matchNumber]
    # Select players on franchise roster
    tableA = df.loc[df.franchiseName==franchiseA]
    tableA.reset_index(inplace=True, drop=True)
    # Create summary row
    rowHead = ["summary", franchiseA, "Total", "", "", ""]
    rowSummary = rowHead + list(tableA.loc[tableA.status=='starter'].sum()[['sharkProjection', 'liveScore', 'secondsRemaining', 'finalProjection']])
    tableA.loc[len(tableA)] = rowSummary
    # Create categories to sort by
    tableA.status = pd.Categorical(tableA.status, 
                        categories=["nonstarter", 'Total', "starter"],
                        ordered=True)
    tableA.Position = pd.Categorical(tableA.Position, 
            categories=['Def', 'PK', 'TE', 'WR', 'RB', 'QB', ""],
            ordered=True)
    # Sort
    tableA.sort_values(['status', 'Position', 'finalProjection'], inplace=True, ascending=False)
    tableA.reset_index(inplace=True, drop=True)
    # Select players on franchise roster
    tableB = df.loc[df.franchiseName==franchiseB]
    tableB.reset_index(inplace=True, drop=True)
    # Create summary row
    rowHead = ["summary", franchiseA, "Total", "", "", ""]
    rowSummary = rowHead + list(tableB.loc[tableB.status=='starter'].sum()[['sharkProjection', 'liveScore', 'secondsRemaining', 'finalProjection']])
    tableB.loc[len(tableB)] = rowSummary
    # Create categories to sort by
    tableB.status = pd.Categorical(tableB.status, 
                        categories=["nonstarter", 'Total', "starter"],
                        ordered=True)
    tableB.Position = pd.Categorical(tableB.Position, 
            categories=['Def', 'PK', 'TE', 'WR', 'RB', 'QB', ""],
            ordered=True)
    # Sort
    tableB.sort_values(['status', 'Position', 'finalProjection'], inplace=True, ascending=False)
    tableB.reset_index(inplace=True, drop=True)
    return render_template(
        "liveScore2.html", 
        M1A=[M1A.to_html(classes='data')],
        M2A=[M2A.to_html(classes='data')],
        M3A=[M3A.to_html(classes='data')],
        M4A=[M4A.to_html(classes='data')],
        M5A=[M5A.to_html(classes='data')],
        M6A=[M6A.to_html(classes='data')], 
        franchiseA=franchiseA,
        franchiseB=franchiseB,
        tableA=[tableA.to_html(classes='data')],
        tableB=[tableB.to_html(classes='data')]
        )