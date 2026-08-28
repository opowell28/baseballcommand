import json

import requests
import datetime

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
    date = datetime.date.today()
    url = f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        # print(json.dumps(data, sort_keys=True, indent=4))

        games = data["dates"][0]["games"]

        # TODO: update this to handle days when no games occur (data["totalGames"])
        for game in games:
            away_team = game["teams"]["away"]["team"]["name"]
            away_score = game["teams"]["away"]["score"]

            home_team = game["teams"]["home"]["team"]["name"]
            home_score = game["teams"]["home"]["score"]

            print(f'{away_team} {away_score} - {home_score} {home_team}')