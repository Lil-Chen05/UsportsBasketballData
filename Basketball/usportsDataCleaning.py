import pandas as pd
import numpy as np
from datetime import datetime

# Load player game data
jerrysFile = pd.read_csv("playerGameData2024-25_processed.csv") # INSERT PLAYER GAME LOG FILE HERE!!

# List of non-Canadian teams to exclude
non_canadian_teams = [
    "Air Force Academy Falcons", "Rhode Island Rams", "Black Hills State Yellow Jackets",
    "Louisville Cardinals", "Saginaw Valley Cardinals", "Albany Great Danes",
    "Catholic University Cardinals", "Heidelberg Student Princes", "Moravian Greyhounds",
    "Macalester Scots", "Hope International", "Benedictine Mesa Redhawks",
    "Western Washington", "Westcliff", "Universidad Panamericana Guada"
]

# Filter out non-Canadian teams
jerrysFile = jerrysFile[~jerrysFile['Opponent'].isin(non_canadian_teams)].copy()

# Load schedule data (bizarre font from excel)
usports_sched = pd.read_csv("Usports Data - Sheet1.csv", header=None) # INCLUDE SEASON SCHEDULE FILE HERE!!

# Rename columns
usports_sched.columns = [f'V{i+1}' for i in range(usports_sched.shape[1])]

# Identify Month rows (V1 contains a month name and V2–V5 are all NA)
usports_sched['Month'] = np.where(
    usports_sched['V1'].str.strip().str.match(
        r"^(January|February|March|April|May|June|July|August|September|October|November|December)$",
        case=False
    ) &
    usports_sched[['V2', 'V3', 'V4', 'V5']].isna().all(axis=1),
    usports_sched['V1'].str.strip(),
    np.nan
)

# Identify Day rows (V1 contains a day, V2-V5 are all NA)
usports_sched['DayText'] = np.where(
    usports_sched['V1'].str.match(r'^\w+\.\s*\d+$'),  
    usports_sched['V1'],
    np.nan
)


pd.set_option('future.no_silent_downcasting', True)

# Fill down Month and DayText
usports_sched['Month'] = usports_sched['Month'].ffill()
usports_sched['DayText'] = usports_sched['DayText'].ffill()

# Filter to only valid game rows
usports_clean = usports_sched[
     ~usports_sched['V1'].isin(['Away', 'Home']) &
     ~usports_sched['V1'].str.match("^[A-Za-z]+$") &
     ~usports_sched['V1'].str.match(r'^\w+\.\s*\d+$') &
     ~((usports_sched['V2'] == '') &
       (usports_sched['V3'] == '') &
       (usports_sched['V4'] == '') &
       (usports_sched['V5'] == '')) ].copy()

# Extract day safely from DayText
usports_clean['Day'] = usports_clean['DayText'].str.extract(r'\D*(\d+)$').astype(float)

# Infer year based on month
usports_clean['Year'] = np.where(
     usports_clean['Month'].isin(['November', 'December']),
     2024,
     2025) # INSERT PROPER YEAR INFO HERE!!!

# Convert full month name to number (strip leading/trailing whitespace just in case)
usports_clean['Month_Num'] = usports_clean['Month'].map(
    lambda m: datetime.strptime(m.strip(), "%B").month if pd.notnull(m) else np.nan)

# Construct ISO date string: YYYY-MM-DD
usports_clean['Date_Str'] = (
     usports_clean['Year'].astype(int).astype(str) + "-" +
     usports_clean['Month_Num'].astype('Int64').astype(str).str.zfill(2) + "-" +
     usports_clean['Day'].astype('Int64').astype(str).str.zfill(2))


# Convert final date string to datetime object
usports_clean['Date'] = pd.to_datetime(
   usports_clean['Date_Str'], format="%Y-%m-%d", errors="coerce")

# Rename and subset
usports_clean = usports_clean.rename(columns={'V1': 'Away', 'V2': 'Home'})
usports_clean = usports_clean[['Date', 'Away', 'Home']].copy()

# Split out team names and scores
usports_clean['Away_Team'] = usports_clean['Away'].str.replace(r'\d+$', '', regex=True).str.strip()
usports_clean['Away_Score'] = usports_clean['Away'].str.extract(r'(\d+)$').astype(int)

usports_clean['Home_Team'] = usports_clean['Home'].str.replace(r'\d+$', '', regex=True).str.strip()
usports_clean['Home_Score'] = usports_clean['Home'].str.extract(r'(\d+)$').astype(int)

usports_clean = usports_clean[['Date', 'Away_Team', 'Away_Score', 'Home_Team', 'Home_Score']]

# Lookup table
team_lookup = {
     "Acadia": "Acadia Axemen",
     "Alberta": "Alberta Golden Bears",
     "Algoma": "Algoma Thunderbirds",
     "Algonquin": "Algonquin Thunder",
     "Bishop's": "Bishop's Gaiters",
     "Brandon": "Brandon Bobcats",
     "Brock": "Brock Badgers",
     "Calgary": "Calgary Dinos",
     "Cape Breton": "Cape Breton Capers",
     "Carleton": "Carleton Ravens",
     "Concordia": "Concordia Stingers",
     "Dalhousie": "Dalhousie Tigers",
     "Guelph": "Guelph Gryphons",
     "Humber College": "Humber Hawks",
     "Lakehead": "Lakehead Thunderwolves",
     "Laurentian": "Laurentian Voyageurs",
     "Laurier": "Wilfrid Laurier Golden Hawks",
     "Laval": "Laval Rouge et Or",
     "Lethbridge": "Lethbridge Pronghorns",
     "MacEwan": "MacEwan Griffins",
     "Manitoba": "Manitoba Bisons",
     "McGill": "McGill Redbirds",
     "McMaster": "McMaster Marauders",
     "Memorial": "Memorial Sea-Hawks",
     "Mohawk College": "Mohawk Mountaineers",
     "Mount Royal": "Mount Royal University Cougars",
     "Nipissing": "Nipissing Lakers",
     "Ontario Tech": "Ontario Tech Ridgebacks",
     "Ottawa": "Ottawa Gee Gees",
     "Queen's": "Queen's Gaels",
     "Regina": "Regina Cougars",
     "Saint Mary's": "Saint Mary's Huskies",
     "Saskatchewan": "Saskatchewan Huskies",
     "Sheridan College": "Sheridan Bruins",
     "St. Thomas": "St. Thomas Tommies",
     "StFX": "St. Francis Xavier X-Men",
     "Thompson Rivers": "Thompson Rivers Wolfpack",
     "TMU": "TMU Bold",
     "Toronto Metropolitan": "TMU Bold",
     "Toronto": "Toronto Varsity Blues",
     "Trinity Western": "Trinity Western Spartans",
     "UBC": "UBC Thunderbirds",
     "UBC Okanagan": "UBC Okanagan Heat",
     "UFV": "UFV Cascades",
     "UNB": "UNB Reds",
     "UNBC": "UNBC Timberwolves",
     "UPEI": "UPEI Panthers",
     "UQAM": "UQAM Citadins",
     "Victoria": "Victoria Vikes",
     "Vancouver Island University": "VIU Mariners",
     "Waterloo": "Waterloo Warriors",
     "Western": "Western Mustangs",
     "Wilfrid Laurier": "Wilfrid Laurier Golden Hawks",
     "Windsor": "Windsor Lancers",
     "Winnipeg": "Winnipeg Wesmen",
     "York": "York Lions"}

usports_clean['Away_Team'] = usports_clean['Away_Team'].map(team_lookup)
usports_clean['Home_Team'] = usports_clean['Home_Team'].map(team_lookup)

# Standardize dates
jerrysFile['Date'] = pd.to_datetime(jerrysFile['Date'])
usports_clean['Date'] = pd.to_datetime(usports_clean['Date'])

# Determine Home/Away
def determine_home_away(row):
     games_today = usports_clean[usports_clean['Date'] == row['Date']]
     if row['Team'] in games_today['Home_Team'].values:
         return 'Home'
     elif row['Team'] in games_today['Away_Team'].values:
         return 'Away'
     else:
         return np.nan

jerrysFile['HomeAway'] = jerrysFile.apply(determine_home_away, axis=1)

# Export cleaned data
jerrysFile.to_csv("2024-25DataCleanFinalPython.csv", index=False) # INSERT DESIRED EXPORT FILE NAME HERE!
