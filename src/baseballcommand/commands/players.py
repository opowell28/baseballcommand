import difflib
import re
import unicodedata
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

BASE_URL = 'https://statsapi.mlb.com/api/v1'

HITTING_COLUMNS = [
    ('G', 'gamesPlayed'), ('AB', 'atBats'), ('R', 'runs'), ('H', 'hits'), ('2B', 'doubles'),
    ('3B', 'triples'), ('HR', 'homeRuns'), ('RBI', 'rbi'), ('SB', 'stolenBases'), ('BB', 'baseOnBalls'),
    ('SO', 'strikeOuts'), ('AVG', 'avg'), ('OBP', 'obp'), ('SLG', 'slg'), ('OPS', 'ops'),
]
PITCHING_COLUMNS = [
    ('G', 'gamesPitched'), ('GS', 'gamesStarted'), ('W', 'wins'), ('L', 'losses'), ('SV', 'saves'),
    ('IP', 'inningsPitched'), ('H', 'hits'), ('ER', 'earnedRuns'), ('BB', 'baseOnBalls'),
    ('SO', 'strikeOuts'), ('HR', 'homeRuns'), ('ERA', 'era'), ('WHIP', 'whip'),
]


def normalize_name(name):
    # Strip accents (Acuña -> acuna), punctuation, and suffixes so user input matches API names
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode()
    name = re.sub(r'[^a-z ]', '', name.lower().replace('-', ' '))
    words = [word for word in name.split() if word not in ('jr', 'sr', 'ii', 'iii', 'iv')]
    return ' '.join(words)


def get_active_players(season):
    response = requests.get(f'{BASE_URL}/sports/1/players?season={season}')
    response.raise_for_status()
    return response.json().get('people', [])


def find_players(name, players):
    target = normalize_name(name)
    names = {}
    for player in players:
        # Match on both the full name and the name the player goes by (e.g. "Mike" vs "Michael")
        keys = {normalize_name(player['fullName']),
                normalize_name(f'{player.get("useName", "")} {player.get("lastName", "")}')}
        for key in keys:
            names.setdefault(key, []).append(player)

    if target in names:
        return names[target]

    close = difflib.get_close_matches(target, names.keys(), n=5, cutoff=0.75)
    matches = []
    for key in close:
        for player in names[key]:
            if player not in matches:
                matches.append(player)
    return matches


def choose_player(matches):
    print('Multiple players found:')
    for i, player in enumerate(matches, start=1):
        print(f'  {i}. {player["fullName"]} ({player["primaryPosition"]["abbreviation"]})')

    try:
        choice = int(input('Select a player: '))
    except (ValueError, EOFError):
        return None
    return matches[choice - 1] if 1 <= choice <= len(matches) else None


def get_season_stats(player_id, group, season):
    response = requests.get(f'{BASE_URL}/people/{player_id}/stats?stats=season&group={group}&season={season}')
    response.raise_for_status()
    stats = response.json().get('stats', [])
    if not stats or not stats[0].get('splits'):
        return None
    # Players traded mid-season have one split per team plus a combined split without a team
    splits = stats[0]['splits']
    combined = [split for split in splits if 'team' not in split]
    return (combined or splits)[-1]['stat']


def print_stats(stat, columns):
    widths = [max(len(label), len(str(stat.get(key, '-')))) for label, key in columns]
    print(' | '.join(label.rjust(width) for (label, _), width in zip(columns, widths)))
    print('-+-'.join('-' * width for width in widths))
    print(' | '.join(str(stat.get(key, '-')).rjust(width) for (_, key), width in zip(columns, widths)))


def player_search(first_name, last_name):
    season = datetime.now(ZoneInfo('America/New_York')).year
    name = f'{first_name} {last_name}'

    try:
        players = get_active_players(season)
        matches = find_players(name, players)
    except requests.RequestException as e:
        print(f'Error searching for player: {e}')
        return

    if not matches:
        print(f'No active MLB player found matching "{name}".')
        return

    player = matches[0] if len(matches) == 1 else choose_player(matches)
    if player is None:
        print('No player selected.')
        return

    if normalize_name(player['fullName']) != normalize_name(name):
        print(f'Showing results for {player["fullName"]}')

    position = player['primaryPosition']
    if position['abbreviation'] == 'TWP':
        groups = ['hitting', 'pitching']
    elif position['type'] == 'Pitcher':
        groups = ['pitching']
    else:
        groups = ['hitting']

    print(f'\n{player["fullName"]} ({position["abbreviation"]}) - {season} Season')
    for group in groups:
        try:
            stat = get_season_stats(player['id'], group, season)
        except requests.RequestException as e:
            print(f'Error retrieving stats: {e}')
            return

        print(f'\n{group.capitalize()}')
        if stat is None:
            print(f'No {group} stats for {season}.')
        else:
            print_stats(stat, HITTING_COLUMNS if group == 'hitting' else PITCHING_COLUMNS)
