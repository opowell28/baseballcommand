import time
from datetime import datetime, timedelta
from itertools import zip_longest
from zoneinfo import ZoneInfo

import requests

from baseballcommand import utils

BASE_URL = 'https://statsapi.mlb.com/api/v1'

# The linescore endpoint is cached by MLB's CDN for 10 seconds, so polling faster returns the same data
MIN_INTERVAL = 10

CLEAR_SCREEN = '\033[H\033[2J'
YELLOW = '\033[33m'
BOLD = '\033[1m'
RESET = '\033[0m'

OCCUPIED = f'{YELLOW}◆{RESET}'
EMPTY = '◇'
DIAMOND_SIZE = 3
NAME_WIDTH = 12


def get_games(today):
    # Include yesterday so games that run past midnight Eastern are still found
    yesterday = (datetime.fromisoformat(today) - timedelta(days=1)).strftime('%Y-%m-%d')
    response = requests.get(f'{BASE_URL}/schedule?sportId=1&startDate={yesterday}&endDate={today}&hydrate=team')
    response.raise_for_status()
    games = [game for date in response.json().get('dates', []) for game in date['games']]
    return [game for game in games
            if game.get('officialDate') == today or game['status']['abstractGameState'] == 'Live']


def team_matches(query, team):
    query = query.lower()
    names = [team.get('name', ''), team.get('teamName', ''), team.get('abbreviation', ''), team.get('locationName', '')]
    return any(query == name.lower() for name in names) or query in team.get('name', '').lower()


def find_games(query, games):
    return [game for game in games
            if team_matches(query, game['teams']['away']['team']) or team_matches(query, game['teams']['home']['team'])]


def game_label(game):
    away = game['teams']['away']['team']['name']
    home = game['teams']['home']['team']['name']
    state = game['status']['detailedState']
    if game['status']['abstractGameState'] == 'Preview':
        state = utils.UTC_to_EST(game['gameDate'])
    return f'{away} @ {home} ({state})'


def choose_game(games):
    print('Games today:')
    for i, game in enumerate(games, start=1):
        print(f'  {i}. {game_label(game)}')

    try:
        choice = int(input('Select a game: '))
    except (ValueError, EOFError):
        return None
    return games[choice - 1] if 1 <= choice <= len(games) else None


def get_linescore(game_pk):
    response = requests.get(f'{BASE_URL}/game/{game_pk}/linescore')
    response.raise_for_status()
    return response.json()


def get_status(game_pk):
    response = requests.get(f'{BASE_URL}/schedule?sportId=1&gamePk={game_pk}'
                            '&fields=dates,games,status,detailedState,abstractGameState')
    response.raise_for_status()
    return response.json()['dates'][0]['games'][0]['status']


def last_name(person):
    return person['fullName'].split(' ', 1)[-1] if person else ''


def dots(count, total):
    return '●' * count + '○' * (total - count)


def render_diamond(offense, size=DIAMOND_SIZE):
    # Drawn on a grid so every base path lines up; each diagonal moves 2 columns per row because
    # terminal cells are about twice as tall as they are wide
    width = 4 * size + 1
    middle = 2 * size
    grid = [[' '] * width for _ in range(2 * size + 1)]
    for i in range(1, size):
        grid[i][middle - 2 * i] = '╱'
        grid[i][middle + 2 * i] = '╲'
        grid[size + i][2 * i] = '╲'
        grid[size + i][width - 1 - 2 * i] = '╱'

    def base(name):
        return OCCUPIED if name in offense else EMPTY

    grid[0][middle] = base('second')
    grid[size][0] = base('third')
    grid[size][width - 1] = base('first')
    grid[size][middle] = '·'
    grid[2 * size][middle] = '⌂'

    # Runner names sit beside their base, and the batter beside home plate
    left = [''] * len(grid)
    right = [''] * len(grid)
    right[0] = last_name(offense.get('second'))
    left[size] = last_name(offense.get('third'))
    right[size] = last_name(offense.get('first'))
    right[2 * size] = last_name(offense.get('batter'))
    return [f'{left[row][:NAME_WIDTH].rjust(NAME_WIDTH)} {"".join(grid[row]).rstrip()} {right[row][:NAME_WIDTH]}'
            .rstrip() for row in range(len(grid))]


def render_line_score(linescore, away, home):
    innings = linescore.get('innings', [])
    count = max(linescore.get('scheduledInnings', 9), len(innings))
    header = ['   '] + [str(i).rjust(2) for i in range(1, count + 1)] + ['  R', '  H', '  E']
    rows = [header]
    for side, abbreviation in (('away', away), ('home', home)):
        cells = [abbreviation.ljust(3)]
        for i in range(count):
            runs = innings[i][side].get('runs') if i < len(innings) else None
            cells.append(str(runs if runs is not None else '').rjust(2))
        totals = linescore.get('teams', {}).get(side, {})
        cells += [str(totals.get(key, 0)).rjust(3) for key in ('runs', 'hits', 'errors')]
        rows.append(cells)
    return [' '.join(row) for row in rows]


def render(game, linescore, status):
    away_team = game['teams']['away']['team']
    home_team = game['teams']['home']['team']
    away = away_team.get('abbreviation', away_team['name'][:3])
    home = home_team.get('abbreviation', home_team['name'][:3])
    teams = linescore.get('teams', {})
    away_runs = teams.get('away', {}).get('runs', 0)
    home_runs = teams.get('home', {}).get('runs', 0)

    lines = [f'{BOLD}{away_team["name"]} @ {home_team["name"]}{RESET}', '']

    if status['abstractGameState'] == 'Preview':
        lines.append(f'{status["detailedState"]} - first pitch at {utils.UTC_to_EST(game["gameDate"])} ET')
        return lines

    if status['abstractGameState'] == 'Final':
        lines.append(f'{status["detailedState"]}: {away} {away_runs} - {home_runs} {home}')
    else:
        arrow = '▲' if linescore.get('isTopInning') else '▼'
        inning = f'{arrow} {linescore.get("currentInningOrdinal", "")}'
        offense = linescore.get('offense', {})
        diamond = render_diamond(offense)
        side = [
            '',
            f'{away.ljust(3)} {str(away_runs).rjust(2)}   {inning}',
            f'{home.ljust(3)} {str(home_runs).rjust(2)}',
            '',
            f'B {dots(linescore.get("balls", 0), 4)}',
            f'S {dots(linescore.get("strikes", 0), 3)}',
            f'O {dots(min(linescore.get("outs", 0), 3), 3)}',
        ]
        lines += [f'{left.ljust(16)}{right}'.rstrip() for left, right in zip_longest(side, diamond, fillvalue='')]
        lines.append('')
        if status['detailedState'] != 'In Progress':
            lines.append(status['detailedState'])
        lines.append(f'Pitching: {last_name(linescore.get("defense", {}).get("pitcher"))}'
                     f'   At bat: {last_name(offense.get("batter"))}')

    lines.append('')
    lines += render_line_score(linescore, away, home)
    return lines


def watch(game, interval):
    game_pk = game['gamePk']
    while True:
        try:
            status = get_status(game_pk)
            linescore = get_linescore(game_pk)
        except requests.RequestException as e:
            print(f'Error retrieving game data: {e}')
            return

        print(CLEAR_SCREEN + '\n'.join(render(game, linescore, status)))
        if status['abstractGameState'] == 'Final' or interval is None:
            return
        print(f'\nUpdating every {interval}s - press Ctrl+C to quit')
        time.sleep(interval)


def live_game(team=None, interval=MIN_INTERVAL, once=False):
    today = datetime.now(ZoneInfo('America/New_York')).strftime('%Y-%m-%d')
    try:
        games = get_games(today)
    except requests.RequestException as e:
        print(f'Error retrieving schedule: {e}')
        return

    if team:
        games = find_games(team, games)
        if not games:
            print(f'No game found today for "{team}".')
            return
    elif not games:
        print('No games scheduled today.')
        return

    live = [game for game in games if game['status']['abstractGameState'] == 'Live']
    if len(games) == 1:
        game = games[0]
    elif len(live) == 1 and team:
        game = live[0]
    else:
        game = choose_game(games)
    if game is None:
        print('No game selected.')
        return

    try:
        watch(game, None if once else max(interval, MIN_INTERVAL))
    except KeyboardInterrupt:
        print()
