import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

def get_leagues():
    # This url responds with just MLB leagues
    url = 'https://statsapi.mlb.com/api/v1/leagues?sportId=1'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        leagues = data["leagues"]

        for league in leagues:
            # filter by AL and NL
            if league["id"] == 103 or league["id"] == 104:
                print(f'League id: {league["id"]} | League name: {league["name"]}')
    else:
        print(f'{response.status_code}')
        return None

def get_todays_schedule():
    date = datetime.today().strftime('%Y-%m-%d')
    url = f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        # print(json.dumps(data, sort_keys=True, indent=4))

        games = data["dates"][0]["games"]

        # TODO: update this to handle days when no games occur (data["dates"][0]["totalGames"])
        for game in games:
            game_date = game["gameDate"]
            # Get datetime from string in JSON response
            dt = datetime.fromisoformat(game_date)
            # Convert UTC to US Eastern time
            eastern_dt = dt.astimezone(ZoneInfo('America/New_York'))
            # Isolate just the time (game_date contains full date and time)
            game_time_eastern = eastern_dt.strftime('%I:%M %p')

            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            print(f'{game_time_eastern} | {away_team} - {home_team}')

    else:
        print(f'Response code: {response.status_code}')
        return None