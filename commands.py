import requests
import json

base_url = 'https://statsapi.mlb.com/api/v1/'

def get_leagues():
    url = base_url + 'leagues'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        leagues = data["leagues"]
        first_league = leagues[0]

        print(f'League id: {first_league["id"]} | League name: {first_league["name"]}')
        return None
    else:
        print(f'{response.status_code}')
        return None

def get_scores():
    pass