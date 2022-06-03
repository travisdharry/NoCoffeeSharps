# Import dependencies
from flask import Flask, render_template
import pandas as pd
from bs4 import BeautifulSoup
import requests
from datetime import date
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go

# import config file
from config import league_id, api_key_MFL



# Create a new Flask instance
app = Flask(__name__)

# Create Flask route
@app.route('/')

# Create a function
def index():
    title = "This is a test title"
    body_message = "Hello, KB!"
    return(render_template('index.html', title=title, body_message=body_message))

# New Route
@app.route("/api/v1.0/compareFranchises")

def compareFranchises():
    # Initialize Franchise data
    franchise_df = pd.DataFrame()
    franchise_df['Franchise'] = ['0001', '0002', '0003', '0004', '0005', '0006', '0007', '0008', '0009', '0010', '0011', '0012', 'FA']
    franchise_df['FranchiseCode'] = ['PMS', 'WFF', 'VER', 'DWS', 'CRO', 'OHS', 'FNF', 'CAM', 'PBW', 'SAS', 'GUS', 'IDK', 'FA']
    franchise_df['FranchiseName'] =['PMS', 
                                    'WFF', 
                                    'VER', 
                                    'DWS', 
                                    'CRO', 
                                    'OHS', 
                                    'FNF', 
                                    'CAM', 
                                    'PBW', 
                                    'SAS', 
                                    'GUS', 
                                    'IDK', 
                                    'FA'
                                    ]

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
    rosters_df.columns=['Franchise','Week','PlayerID','RosterStatus']

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
    complete = player_df.merge(rosters_df, on='PlayerID').merge(franchise_df[['Franchise', 'FranchiseCode']], on='Franchise').merge(shark_df, on='PlayerID').merge(adp_df, on='PlayerID')
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

    qbs = pd.read_excel("data/RelativeValues2021.xlsx", sheet_name="QB")
    rbs = pd.read_excel("data/RelativeValues2021.xlsx", sheet_name="RB")
    wrs = pd.read_excel("data/RelativeValues2021.xlsx", sheet_name="WR")
    tes = pd.read_excel("data/RelativeValues2021.xlsx", sheet_name="TE")
    pks = pd.read_excel("data/RelativeValues2021.xlsx", sheet_name="PK")
    defs = pd.read_excel("data/RelativeValues2021.xlsx", sheet_name="DEF")

    qbs = qbs['Regressed']
    rbs = rbs['Regressed']
    wrs = wrs['Regressed']
    tes = tes['Regressed']
    pks = pks['Regressed']
    defs = defs['Regressed']

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

    today = result[result['Date'] == date.today()].sort_values(by='Regressed', ascending=False, ignore_index=True)

    qbs_rostered = today[today['Position'] == "QB"]
    qbs_rostered.reset_index(inplace=True, drop=True)
    rbs_rostered = today[today['Position'] == "RB"]
    rbs_rostered.reset_index(inplace=True, drop=True)
    wrs_rostered = today[today['Position'] == "WR"]
    wrs_rostered.reset_index(inplace=True, drop=True)
    tes_rostered = today[today['Position'] == "TE"]
    tes_rostered.reset_index(inplace=True, drop=True)

    qbs_top = qbs_rostered.sort_values(by='Regressed', ascending=False, ignore_index=True).groupby('FranchiseCode').head(1)
    rbs_top = rbs_rostered.sort_values(by='Regressed', ascending=False, ignore_index=True).groupby('FranchiseCode').head(2)
    wrs_top = wrs_rostered.sort_values(by='Regressed', ascending=False, ignore_index=True).groupby('FranchiseCode').head(3)
    tes_top = tes_rostered.sort_values(by='Regressed', ascending=False, ignore_index=True).groupby('FranchiseCode').head(2)

    qbs_remainder = qbs_rostered[~qbs_rostered['PlayerID'].isin(qbs_top['PlayerID'])].groupby('FranchiseCode').head(1)
    rbs_remainder = rbs_rostered[~rbs_rostered['PlayerID'].isin(rbs_top['PlayerID'])].groupby('FranchiseCode').head(3)
    wrs_remainder = wrs_rostered[~wrs_rostered['PlayerID'].isin(wrs_top['PlayerID'])].groupby('FranchiseCode').head(3)
    tes_remainder = tes_rostered[~tes_rostered['PlayerID'].isin(tes_top['PlayerID'])].groupby('FranchiseCode').head(3)
                                                            
    remainder = pd.concat([qbs_remainder, rbs_remainder, wrs_remainder, tes_remainder])
                                
    top_remainders = remainder.sort_values(by='Regressed', ascending=False, ignore_index=True).groupby('FranchiseCode').head(3)
                                
    fran_rost = pd.concat([qbs_top, rbs_top, wrs_top, tes_top, top_remainders])
    fran_rost = fran_rost.sort_values(by='Regressed', ascending=False, ignore_index=True)

    fran_rank = fran_rost.groupby('FranchiseCode').sum().sort_values(by='Regressed', ascending=False)

    sorter = fran_rank.index

    fran_rost.FranchiseCode = fran_rost.FranchiseCode.astype("category")
    fran_rost.FranchiseCode.cat.set_categories(sorter, inplace=True)
    fran_rost.sort_values(["FranchiseCode"], inplace=True)

    fig = px.bar(fran_rost, 
                x="FranchiseCode", 
                y="Regressed", 
                color="Position", 
                text='Name', 
                color_discrete_map={
                    "RB": "#1033a6", #blue #1033a6 #0c2987
                    "TE": "#1295ad", #teal #02687b #038097
                    "WR": "#643fc1", #purple #4f22bc #643fc1
                    "QB": "#f5d000"}, #gold #f5d000
                category_orders={
                    "Position": ["RB", "QB", "WR", "TE"]}
                )
    fig.update_layout(barmode='stack', xaxis={'categoryorder':'total descending'})

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('compareFranchises.html', graphJSON=graphJSON)