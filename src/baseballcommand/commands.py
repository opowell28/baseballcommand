import json
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from . import utils


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
        return
    else:
        print(f'{response.status_code}')
        return

def get_todays_schedule():
    date = datetime.now(tz=ZoneInfo('America/New_York')).strftime('%Y-%m-%d')
    url = f'https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date}'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        # print(json.dumps(data, sort_keys=True, indent=4))
        games = data["dates"][0]["games"]

        # TODO: update this to handle days when no games occur (data["dates"][0]["totalGames"])
        for game in games:
            game_status = game["status"]["detailedState"]

            game_date = game["gameDate"]
            game_time_eastern = utils.UTC_to_EST(game_date)

            away_team = game["teams"]["away"]["team"]["name"]
            home_team = game["teams"]["home"]["team"]["name"]

            # Game has not yet started
            if game_status == 'Scheduled':
                print(f'{game_time_eastern} | {away_team} - {home_team}')
            # Game is in-progress
            elif game_status == 'Live':
                # TODO: need to adjust game status matching
                #TODO: I believe this needs to be pulled from a "game" object
                away_score = game["teams"]["away"]["score"]
                home_score = game["teams"]["home"]["score"]
                print(f'{away_team} {away_score} - {home_score} {home_team}')
            elif game_status == 'Final':
                #TODO: need to adjust game status matching
                away_score = game["teams"]["away"]["score"]
                home_score = game["teams"]["home"]["score"]
                print(f'Final: {away_team} {away_score} - {home_score} {home_team}')
        return
    else:
        print(f'Response code: {response.status_code}')
        return