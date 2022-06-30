# Import dependencies
from flask import Flask, render_template, request
import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import date
import json
import os
import plotly
import plotly.express as px
import plotly.graph_objects as go


# Create a new Flask instance
app = Flask(__name__)

# Create Flask route
@app.route('/')
def index():
    return render_template("index.html")

# Create Flask route
@app.route('/compare')

# Create a function
def compareFranchises():

    league_id = request.args.get("leagueID")

    # Get Franchises in the league
    urlString = f"https://www54.myfantasyleague.com/2022/export?TYPE=league&L={league_id}"
    response = requests.get(urlString)
    soup = BeautifulSoup(response.content,'xml')

    data = []
    franchises = soup.find_all('franchise')
    for i in range(len(franchises)):
        rows = [franchises[i].get("id"), franchises[i].get("name")]
        data.append(rows)
    franchise_df = pd.DataFrame(data)
    franchise_df.columns=['FranchiseID','FranchiseName']
    franchise_df = franchise_df.append({"FranchiseID":"FA", "FranchiseName":"Free Agent"}, ignore_index=True)

    # Get all players' name, team name, position
    urlString = "https://api.myfantasyleague.com/2022/export?TYPE=players"
    response = requests.get(urlString)
    soup = BeautifulSoup(response.content,'xml')

    data = []
    players = soup.find_all('player')
    for i in range(len(players)):
        rows = [players[i].get("id"), players[i].get("name"), players[i].get("position"), players[i].get("team")]
        data.append(rows)
    player_df = pd.DataFrame(data)
    player_df.columns=['PlayerID','Name', 'Position', 'Team']
    
    # Get franchise rosters
    urlString = f"https://www54.myfantasyleague.com/2022/export?TYPE=rosters&L={league_id}"
    response = requests.get(urlString)
    soup = BeautifulSoup(response.content,'xml')

    data = []
    franchises = soup.find_all('franchise')
    for i in range(0,len(franchises)):
        current_franchise = franchises[i].find_all('player')
        for j in range(0,len(current_franchise)):
            rows = [franchises[i].get("id"), franchises[i].get("week"), current_franchise[j].get("id"), current_franchise[j].get("status")]
            data.append(rows)
    rosters_df = pd.DataFrame(data)

    # Get Free Agents
    urlString = f"https://www54.myfantasyleague.com/2022/export?TYPE=freeAgents&L={league_id}"
    response = requests.get(urlString)
    soup = BeautifulSoup(response.content,'xml')

    data = []
    freeAgents = soup.find_all('player')
    for i in range(len(freeAgents)):
        rows = ["FA", "", freeAgents[i].get("id"), "Free Agent"]
        data.append(rows)
    fa_df = pd.DataFrame(data)
    rosters_df = rosters_df.append(fa_df)
    rosters_df.columns=['FranchiseID','Week','PlayerID','RosterStatus']

    # Get Shark Ranks
    urlString = "https://api.myfantasyleague.com/2022/export?TYPE=playerRanks"
    response = requests.get(urlString)
    soup = BeautifulSoup(response.content,'xml')

    data = []
    sharkRanks = soup.find_all('player')
    for i in range(len(sharkRanks)):
        rows = [sharkRanks[i].get("id"), sharkRanks[i].get("rank")]
        data.append(rows)
    shark_df = pd.DataFrame(data)
    shark_df.columns=['PlayerID','SharkRank']
    shark_df['SharkRank'] = shark_df['SharkRank'].astype('int32')

    # Get adp
    urlString = "https://api.myfantasyleague.com/2022/export?TYPE=adp"
    response = requests.get(urlString)
    soup = BeautifulSoup(response.content,'xml')

    data = []
    players = soup.find_all('player')
    for i in range(len(players)):
        rows = [players[i].get("id"), players[i].get("averagePick")]
        data.append(rows)
    adp_df = pd.DataFrame(data)
    adp_df.columns=['PlayerID','ADP']
    adp_df['ADP'] = adp_df['ADP'].astype('float32')

    # Merge all dfs
    complete = player_df.merge(rosters_df, on='PlayerID', how='left').merge(franchise_df[['FranchiseID', 'FranchiseName']], on='FranchiseID', how='left').merge(shark_df, on='PlayerID', how='left').merge(adp_df, on='PlayerID', how='left')
    complete['FranchiseID'].fillna("FA", inplace=True)
    complete['FranchiseName'].fillna("Free Agent", inplace=True)
    complete['RosterStatus'].fillna("Free Agent", inplace=True)
    complete['SharkRank'].fillna(3000, inplace=True)
    complete['ADP'].fillna(3000, inplace=True)
    complete = complete.sort_values(by=['SharkRank'])
    complete.reset_index(inplace=True, drop=True)

    qbs_2022 = complete[complete['Position'] == "QB"]
    qbs_2022.reset_index(inplace=True, drop=True)
    rbs_2022 = complete[complete['Position'] == "RB"]
    rbs_2022.reset_index(inplace=True, drop=True)
    wrs_2022 = complete[complete['Position'] == "WR"]
    wrs_2022.reset_index(inplace=True, drop=True)
    tes_2022 = complete[complete['Position'] == "TE"]
    tes_2022.reset_index(inplace=True, drop=True)
    pks_2022 = complete[complete['Position'] == "PK"]
    pks_2022.reset_index(inplace=True, drop=True)
    defs_2022 = complete[complete['Position'] == "Def"]
    defs_2022.reset_index(inplace=True, drop=True)

    qbs = pd.read_excel("data/RelativeValues.xlsx", sheet_name="QB")
    rbs = pd.read_excel("data/RelativeValues.xlsx", sheet_name="RB")
    wrs = pd.read_excel("data/RelativeValues.xlsx", sheet_name="WR")
    tes = pd.read_excel("data/RelativeValues.xlsx", sheet_name="TE")
    pks = pd.read_excel("data/RelativeValues.xlsx", sheet_name="PK")
    defs = pd.read_excel("data/RelativeValues.xlsx", sheet_name="DEF")

    qbs = qbs[['Projection_Relative', "Projection_Absolute"]]
    rbs = rbs[['Projection_Relative', "Projection_Absolute"]]
    wrs = wrs[['Projection_Relative', "Projection_Absolute"]]
    tes = tes[['Projection_Relative', "Projection_Absolute"]]
    pks = pks[['Projection_Relative', "Projection_Absolute"]]
    defs = defs[['Projection_Relative', "Projection_Absolute"]]


    # Merge dfs
    qbs_2022 = pd.merge(qbs_2022, qbs, how="left", left_index=True, right_index=True)
    rbs_2022 = pd.merge(rbs_2022, rbs, how="left", left_index=True, right_index=True)
    wrs_2022 = pd.merge(wrs_2022, wrs, how="left", left_index=True, right_index=True)
    tes_2022 = pd.merge(tes_2022, tes, how="left", left_index=True, right_index=True)
    pks_2022 = pd.merge(pks_2022, pks, how="left", left_index=True, right_index=True)
    defs_2022 = pd.merge(defs_2022, defs, how="left", left_index=True, right_index=True)
    analyzed = pd.concat([qbs_2022, rbs_2022, wrs_2022, tes_2022, pks_2022, defs_2022])

    analyzed['Date'] = date.today()
    priorWeeks = pd.read_csv("data/2022Values.csv", index_col=0)
    priorWeeks['Date'] = pd.to_datetime(priorWeeks['Date'])
    result = pd.concat([priorWeeks, analyzed], axis=0, ignore_index=True)

    today = result[result['Date'] == date.today()].sort_values(by='Projection_Relative', ascending=False, ignore_index=True)   
    qbs_rostered = today[today['Position'] == "QB"]
    qbs_rostered.reset_index(inplace=True, drop=True)
    rbs_rostered = today[today['Position'] == "RB"]
    rbs_rostered.reset_index(inplace=True, drop=True)
    wrs_rostered = today[today['Position'] == "WR"]
    wrs_rostered.reset_index(inplace=True, drop=True)
    tes_rostered = today[today['Position'] == "TE"]
    tes_rostered.reset_index(inplace=True, drop=True)

    qbs_top = qbs_rostered.sort_values(by='Projection_Relative', ascending=False, ignore_index=True).groupby('FranchiseName').head(1)
    rbs_top = rbs_rostered.sort_values(by='Projection_Relative', ascending=False, ignore_index=True).groupby('FranchiseName').head(2)
    wrs_top = wrs_rostered.sort_values(by='Projection_Relative', ascending=False, ignore_index=True).groupby('FranchiseName').head(3)
    tes_top = tes_rostered.sort_values(by='Projection_Relative', ascending=False, ignore_index=True).groupby('FranchiseName').head(2)

    qbs_remainder = qbs_rostered[~qbs_rostered['PlayerID'].isin(qbs_top['PlayerID'])].groupby('FranchiseName').head(1)
    rbs_remainder = rbs_rostered[~rbs_rostered['PlayerID'].isin(rbs_top['PlayerID'])].groupby('FranchiseName').head(3)
    wrs_remainder = wrs_rostered[~wrs_rostered['PlayerID'].isin(wrs_top['PlayerID'])].groupby('FranchiseName').head(3)
    tes_remainder = tes_rostered[~tes_rostered['PlayerID'].isin(tes_top['PlayerID'])].groupby('FranchiseName').head(3)
                                                            
    remainder = pd.concat([qbs_remainder, rbs_remainder, wrs_remainder, tes_remainder])
                                
    top_remainders = remainder.sort_values(by='Projection_Absolute', ascending=False, ignore_index=True).groupby('FranchiseName').head(3)
                                
    fran_rost = pd.concat([qbs_top, rbs_top, wrs_top, tes_top, top_remainders])
    fran_rost = fran_rost.sort_values(by='Projection_Relative', ascending=False, ignore_index=True)


    fran_rank = fran_rost.groupby('FranchiseName').sum().sort_values(by='Projection_Relative', ascending=False)

    sorter = fran_rank.index

    fran_rost.FranchiseName = fran_rost.FranchiseName.astype("category")
    fran_rost.FranchiseName.cat.set_categories(sorter, inplace=True)
    fran_rost.sort_values(["FranchiseName"], inplace=True)

    fig = px.bar(fran_rost, 
                x="FranchiseName", 
                y="Projection_Relative", 
                color="Position", 
                text='Name', 
                color_discrete_map={
                    "RB": "#062647", #blue #1033a6 #0c2987 1033a6
                    "TE": "#43B3AE", #teal #02687b #038097 1295ad
                    "WR": "#621B74", #purple #4f22bc #643fc1 643fc1
                    "QB": "#ffa524"}, #gold #f5d000 f5d000
                category_orders={
                    "Position": ["RB", "QB", "WR", "TE"]}
                )
    fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('compareFranchises.html', graphJSON=graphJSON)