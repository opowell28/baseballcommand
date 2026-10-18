
import requests


# TODO: improve name matching. Example: searching for Pete Crowe-Armstrong returns Pete Alonso
# solution: check name match on JSON return?
def player_search(first_name, last_name):
    url = (f'https://statsapi.mlb.com/api/v1/people/search?names={first_name.lower()}%20'
           f'{last_name.lower()}'
           f'&active=True'
           f'&sportIDs=1'
           f'&limit=1')

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        # print(json.dumps(data, sort_keys=True, indent=4))

        player = data["people"][0]
        player_id = player["id"]

        # TODO: change URL if player is a pitcher
        stats_url = f'https://statsapi.mlb.com/api/v1/people/{player_id}/stats?stats=season&group=hitting'

        stats_response = requests.get(stats_url)

        if stats_response.status_code == 200:
            # stats_data = stats_response.json()

            # print(json.dumps(stats_data, sort_keys=True, indent=4))

            # stat = stats_data["stats"][0]["splits"][0]["stat"]
            print(f'{"Games Played | ":14}{"At Bats | ":9}{"Hits | ":6}{"Runs | ":6}{"RBI | ":5}{"Home Runs | ":11}'
                  f'{"Doubles | ":9}{"Triples | ":9}{"AVG | ":5}{"OBP | ":5}{"OPS | ":5}{"SLG | ":5}')
            print('-' * 100)

    else:
        print(f'Response: {response.status_code}')
        return