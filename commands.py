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