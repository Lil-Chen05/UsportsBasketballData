import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import sys
import os



BASE_URL = "https://usportshoops.ca"


def get_last_seasons(n=4):
    """
    1) Fetch "Past Seasons" page at BASE_URL/history/pastseasons.php?Gender=MBB
    2) Look for links like /history/seasongames.php?Gender=MBB&Season=YYYY-YY
    3) Return up to the first n unique season strings (e.g. "2024-25")
    """
    url = f"{BASE_URL}/history/pastseasons.php?Gender=MBB"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch seasons page: {e}", file=sys.stderr)
        return []
        
    soup = BeautifulSoup(resp.text, "html.parser")

    seasons = []
    pattern = re.compile(r"seasongames\.php\?Gender=MBB&Season=([0-9]{4}-[0-9]{2})")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        m = pattern.search(href)
        if m:
            season = m.group(1)
            if season not in seasons:
                seasons.append(season)
            if len(seasons) >= n:
                break

    if not seasons:
        print("WARNING:  No seasons found. HTML may have changed.", file=sys.stderr)
    return seasons


def get_game_links_for_season(season):
    """
    Given a season string (e.g. "2022-23"), fetch
      /history/seasongames.php?Gender=MBB&Season=<season>
    and return all full URLs whose href matches
      /history/show-game-report.php?Gender=MBB&Season=<season>&Gameid=…
    Only return links that have a "Stats" link (indicating box score availability)
    """
    url = f"{BASE_URL}/history/seasongames.php?Gender=MBB&Season={season}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"ERROR: Failed to fetch games for season {season}: {e}", file=sys.stderr)
        return []
        
    soup = BeautifulSoup(resp.text, "html.parser")

    game_links = []
    pattern = re.compile(
        r"/history/show-game-report\.php\?Gender=MBB&Season="
        + re.escape(season)
        + r"&Gameid="
    )
    
    # Look for links with "Stats" text to ensure box score exists
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Check if this is a stats link and contains "Stats" text
        if pattern.search(href) and a.get_text(strip=True).lower() == "stats":
            full_url = BASE_URL + href
            if full_url not in game_links:
                game_links.append(full_url)

    if not game_links:
        print(f"WARNING:  No box‐score links found for {season}.", file=sys.stderr)
    else:
        print(f"   Stats Found {len(game_links)} games with box scores for {season}")
        
    return game_links


def extract_game_info(game_url):
    """
    Fetch the box‐score page at game_url and return a dict with:
      'date'     → e.g. "Mon Jul 29, 2024"
      'location' → e.g. "Toronto, ON"
      'team1'    → e.g. "McMaster Marauders"
      'score1'   → e.g. "76"
      'team2'    → e.g. "Air Force Academy Falcons"
      'score2'   → e.g. "87"
    """
    game_info = {
        'date': '',
        'location': '',
        'team1': '',
        'score1': '',
        'team2': '',
        'score2': ''
    }

    try:
        resp = requests.get(game_url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"   ERROR: Could not fetch {game_url}: {e}")
        return game_info

    soup = BeautifulSoup(resp.text, "html.parser")

    # 1) Find the <h2> header, then its next sibling <table>, then inside that
    #    look for any <td> whose text starts with "Date:" or "Location:".
    heading = soup.find("h2", string=re.compile(r"Men's Basketball Game Report"))
    if heading:
        parent_table = heading.find_next_sibling("table")
        if parent_table:
            nested_left = parent_table.find("table")
            if nested_left:
                for td in nested_left.find_all("td"):
                    txt = td.get_text(strip=True)
                    # If the <td> has something like "Date:Mon Jul 29, 2024"
                    if txt.startswith("Date:"):
                        game_info['date'] = txt.replace("Date:", "").strip()
                    elif txt.startswith("Location:"):
                        game_info['location'] = txt.replace("Location:", "").strip()
                # At this point, date/location should be set (if present)

    # 2) Now locate team names & scores. We look again under any
    #    <table border="0" cellpadding="1" cellspacing="1">. In each <tr> with
    #    exactly two <td>s where the right <td> is a digit (the score), we extract.
    team_count = 0
    pattern_strip_digits = re.compile(r"^(.+?)(?:\d*)$")
    for table in soup.find_all("table", {"border": "0", "cellpadding": "1", "cellspacing": "1"}):
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) == 2:
                left_text  = cells[0].get_text(strip=True)
                right_text = cells[1].get_text(strip=True)
                # Only consider rows where right_text is purely digits (the score)
                if cells[1].get("align") == "right" and right_text.isdigit():
                    # Strip any trailing digits from the team name
                    m = pattern_strip_digits.match(left_text)
                    team_name = m.group(1).strip()
                    if team_count == 0:
                        game_info['team1']  = team_name
                        game_info['score1'] = right_text
                    elif team_count == 1:
                        game_info['team2']  = team_name
                        game_info['score2'] = right_text
                        return game_info
                    team_count += 1

    return game_info

        
def parse_boxscore_page(game_url, season):
    """
    Fetches a single game box score page, extracts player stats for both teams,
    and returns a DataFrame with one row per player. Relies on extract_game_info()
    (defined elsewhere) to pull date, location, and team1/team2 names.
    """
    try:
        resp = requests.get(game_url, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"   ERROR: Request failed for {game_url}: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(resp.text, "html.parser")
    game_info = extract_game_info(game_url)
    
            # Fallback for Date/Location
    if not game_info.get("date"):
        for td in soup.find_all("td"):
            if td.get_text(strip=True) == "Date:":
                next_td = td.find_next_sibling("td")
                if next_td:
                    game_info["date"] = next_td.get_text(strip=True)
                break

    if not game_info.get("location"):
        for td in soup.find_all("td"):
            if td.get_text(strip=True) == "Location:":
                next_td = td.find_next_sibling("td")
                if next_td:
                    game_info["location"] = next_td.get_text(strip=True)
                break
    # ───────────────────────────────────────────────────────

   
    print(f"    Processing: Game date = '{game_info.get('date', '')}'")
    print(f"    Processing: Game location = '{game_info.get('location', '')}'")

    # 1) Find the <table> containing "<td colspan='26'>…</td>" (the box‐score container)
    stats_table = None
    for table in soup.find_all("table"):
        if table.find("td", attrs={"colspan": "26"}):
            stats_table = table
            break

    if stats_table is None:
        print(f"   WARNING:  No stats table found at {game_url}")
        return pd.DataFrame()

    records = []
    rows = stats_table.find_all("tr")
    i = 0

    while i < len(rows):
        row = rows[i]
        lead_td = row.find("td", attrs={"colspan": "26"})
        if lead_td:
            bold = lead_td.find("b")
            if not bold:
                i += 1
                continue

            bold_txt = bold.get_text(strip=True)  # e.g. "Windsor Lancers 78"
            m = re.match(r"^(.+?)\s+(\d+)$", bold_txt)
            if not m:
                i += 1
                continue

            player_team = m.group(1).strip()
            # Determine opponent by comparing to game_info['team1'] / ['team2']
            if player_team == game_info.get("team1"):
                opponent = game_info.get("team2", "")
            else:
                opponent = game_info.get("team1", "")

            print(f"    Processing team: {player_team} (vs {opponent})")

            # Skip the next row (header), then start reading players at i+2
            j = i + 2
            while j < len(rows):
                r = rows[j]
                # If we hit a "Totals" row, break out of this team's block
                total_td = r.find("td", attrs={"colspan": "3", "align": "left"})
                if total_td and "Totals" in total_td.get_text():
                    break

                # 2) Grab the entire <tr> text with "|" between each <td>, then split
                raw = r.get_text("|", strip=True)
                fields_all = raw.split("|")
                # 3) Filter out any empty strings caused by consecutive "|" or blank <td>
                fields = [f for f in fields_all if f.strip() != ""]

                if len(fields) == 18:
                    # Now fields[2] becomes "^", shifting the other stats one slot right
                    fields.insert(2, "^")

                # Now we expect exactly 19 fields:
                # [ Jersey, Name(+maybe "*"), StarterFlag or "", Mins,
                #   3Pt_MA, 3PtPct, FG_MA, FGPct, FT_MA, FTPct,
                #   OffReb, DefReb, TotReb, PF, AST, TO, BLK, STL, Pts ]
                if len(fields) == 19:
                    jersey_cell  = fields[0]
                    name_cell    = fields[1]
                    starter_cell = fields[2]
                    if starter_cell == "*":
                        starter_flag = "1" 
                        player_name  = name_cell.replace("*", "").strip()
                    else:
                        starter_flag = "0" 
                        player_name  = name_cell

                    rec = {
                        "Season":           season,
                        "Date":             game_info.get("date", ""),
                        "Location":         game_info.get("location", ""),
                        "Team":             player_team,
                        "Opponent":         opponent,
                        "Jersey":           jersey_cell,
                        "PlayerName":       player_name,
                        "StarterFlag":      starter_flag,
                        "Mins":             fields[3],
                        "ThreePt_Made_Att": fields[4],
                        "ThreePtPct":       fields[5],
                        "FG_Made_Att":      fields[6],
                        "FGPct":            fields[7],
                        "FT_Made_Att":      fields[8],
                        "FTPct":            fields[9],
                        "Reb_Off":          fields[10],
                        "Reb_Def":          fields[11],
                        "Reb_Tot":          fields[12],
                        "PF":               fields[13],
                        "AST":              fields[14],
                        "TO":               fields[15],
                        "BLK":              fields[16],
                        "STL":              fields[17],
                        "Pts":              fields[18],
                    }

                    # Skip any header rows where player_name starts with "Player"
                    if player_name and not player_name.lower().startswith("player"):
                        records.append(rec)
                        print(f"     SUCCESS: Added {jersey_cell} – {player_name} (Starter={starter_flag})")
                else:
                    # If this is the “team‐…” row (team totals), skip with a different message
                    if fields and fields[0].startswith("team-"):
                        print("     WARNING: Team Total Statistics Skipped")
                    else:
                        print(f"     WARNING:  Unexpected field count ({len(fields)}) in row: {fields_all}")

                j += 1

            # Move i past this team's totals row
            i = j + 1
            continue

        i += 1

    if records:
        print(f"    SUCCESS: Extracted {len(records)} player records")
    else:
        print(f"    WARNING:  No player records found in this box score")

    return pd.DataFrame(records)


def scrape_last_four_seasons():
    """
    Enhanced scraping with better progress tracking and error handling
    """
    # Create PlayerData directory if it doesn't exist
    player_data_dir = "PlayerData"
    os.makedirs(player_data_dir, exist_ok=True)

    seasons = get_last_seasons(n=4)
    if not seasons:
        print("ERROR: No seasons found, exiting...")
        return
    seasons = list(reversed(seasons))

    print(f" Found seasons: {', '.join(seasons)}")
    
    for season_idx, season in enumerate(seasons):
        print(f"\n{'='*60}")
        print(f"IN PROGRESS:  SCRAPING SEASON: {season} ({season_idx + 1}/4)")
        print(f"{'='*60}")
        
        links = get_game_links_for_season(season)
        if not links:
            print(f"WARNING:  No games found for {season}, skipping...")
            continue
            
        season_records = []
        games_saved_count = 0
        successful_games = 0

        for idx, game_link in enumerate(links, start=1):
            print(f"\n   Game [{idx}/{len(links)}]: {game_link.split('Gameid=')[-1] if 'Gameid=' in game_link else 'Unknown'}")
            
            df_game = parse_boxscore_page(game_link, season)
            
            if df_game.empty:
                print(f"   WARNING:  No data extracted from this game")
                continue

            season_records.append(df_game)
            games_saved_count += 1
            successful_games += 1

            # Checkpoint after 5 games in the first season
            if season_idx == 0 and games_saved_count == 5:
                checkpoint_df = pd.concat(season_records, ignore_index=True)
                checkpoint_filename = os.path.join(player_data_dir, f"playerGameData{season}_first5.csv")
                checkpoint_df.to_csv(checkpoint_filename, index=False)
                print(f"      CHECKPOINT: First 5 games saved to {checkpoint_filename}")

            # Delay between requests
            time.sleep(0.3)

        # Save season data
        if season_records:
            season_df = pd.concat(season_records, ignore_index=True)
            print(f"\n   Stats Season {season} Summary:")
            print(f"   • Total games processed: {len(links)}")
            print(f"   • Games with data: {successful_games}")
            print(f"   • Total player records: {len(season_df)}")
        else:
            season_df = pd.DataFrame()
            print(f"\n   WARNING:  No data collected for season {season}")

        filename = os.path.join(player_data_dir, f"playerGameData{season}.csv")
        season_df.to_csv(filename, index=False)
        print(f"   SUCCESS  Season data saved: {filename}")
        master_filename = os.path.join(player_data_dir, "playerGameDataAll.csv")
        if os.path.exists(master_filename):
            season_df.to_csv(master_filename, mode='a', header=False, index=False)
        else:
            season_df.to_csv(master_filename, index=False)
    
        # Break between seasons
        if season_idx < len(seasons) - 1:
            print(f"\n   LOADING:  Taking a 3-second break before next season...")
            time.sleep(3)

    print(f"\n{'='*60}")
    print(" SCRAPING COMPLETE!")
    print("📁  Check your directory for the following files:")
    for season in seasons:
        print(f"   • playerGameData{season}.csv")
    if len(seasons) > 0:
        print(f"   • playerGameData{seasons[0]}_first5.csv (checkpoint)")
    print(f"{'='*60}")


if __name__ == "__main__":
    scrape_last_four_seasons()