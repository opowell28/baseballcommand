import re

import pytest

from baseballcommand.commands import live


def make_game(game_pk, away, away_abbr, home, home_abbr, state='Live', detailed='In Progress'):
    return {
        'gamePk': game_pk,
        'gameDate': '2026-10-29T00:08:00Z',
        'officialDate': '2026-10-28',
        'status': {'abstractGameState': state, 'detailedState': detailed},
        'teams': {
            'away': {'team': {'name': away, 'teamName': away.split()[-1], 'abbreviation': away_abbr}},
            'home': {'team': {'name': home, 'teamName': home.split()[-1], 'abbreviation': home_abbr}},
        },
    }


RAYS_BREWERS = make_game(1, 'Tampa Bay Rays', 'TB', 'Milwaukee Brewers', 'MIL')
CUBS_METS = make_game(2, 'Chicago Cubs', 'CHC', 'New York Mets', 'NYM', 'Preview', 'Scheduled')
GAMES = [RAYS_BREWERS, CUBS_METS]

LINESCORE = {
    'currentInningOrdinal': '9th',
    'isTopInning': True,
    'scheduledInnings': 9,
    'innings': [{'num': 1, 'away': {'runs': 0}, 'home': {'runs': 2}}, {'num': 2, 'away': {'runs': 1}, 'home': {}}],
    'teams': {'away': {'runs': 1, 'hits': 4, 'errors': 0}, 'home': {'runs': 2, 'hits': 5, 'errors': 1}},
    'offense': {'batter': {'fullName': 'Josh Lowe'}, 'second': {'fullName': 'Junior Caminero'},
                'third': {'fullName': 'Chandler Simpson'}},
    'defense': {'pitcher': {'fullName': 'Trevor Megill'}},
    'balls': 2, 'strikes': 1, 'outs': 1,
}
LIVE = {'abstractGameState': 'Live', 'detailedState': 'In Progress'}


def plain(lines):
    return [re.sub(r'\033\[[0-9;]*m', '', line) for line in lines]


@pytest.mark.parametrize('query, expected', [
    ('TB', [RAYS_BREWERS]),
    ('brewers', [RAYS_BREWERS]),
    ('Milwaukee Brewers', [RAYS_BREWERS]),
    ('cubs', [CUBS_METS]),
    ('Yankees', []),
])
def test_find_games(query, expected):
    assert live.find_games(query, GAMES) == expected


def test_diamond_marks_occupied_bases():
    diamond = plain(live.render_diamond({'first': {'fullName': 'Yandy Díaz'}, 'third': {'fullName': 'Chandler Simpson'}}))
    assert diamond[0].strip() == '◇'
    assert diamond[3].split() == ['Simpson', '◆', '·', '◆', 'Díaz']


def test_diamond_base_paths_line_up():
    diamond = plain(live.render_diamond({}))
    # Second base, the mound, and home plate share a column, and each path is symmetric around it
    middle = diamond[0].index('◇')
    assert diamond[3].index('·') == middle
    assert diamond[6].index('⌂') == middle
    for row in (1, 2, 4, 5):
        line = diamond[row]
        assert middle - line.index(line.strip()[0]) == line.rindex(line.strip()[-1]) - middle


def test_diamond_truncates_long_names():
    diamond = plain(live.render_diamond({'third': {'fullName': 'Someone Extraordinarilylongname'}}))
    assert diamond[3].split()[0] == 'Extraordinar'
    assert diamond[3].index('◆') == diamond[0].index('◇') - 2 * live.DIAMOND_SIZE


def test_render_live_game():
    lines = plain(live.render(RAYS_BREWERS, LINESCORE, LIVE))
    text = '\n'.join(lines)
    assert 'TB   1   ▲ 9th' in text
    assert 'B ●●○○' in text and 'S ●○○' in text and 'O ●○○' in text
    assert 'Pitching: Megill   At bat: Lowe' in text
    assert '◆ Caminero' in text and 'Simpson ◆' in text and '⌂ Lowe' in text
    assert lines[-2].split() == ['TB', '0', '1', '1', '4', '0']
    assert lines[-1].split() == ['MIL', '2', '2', '5', '1']


def test_render_final_game_skips_diamond():
    lines = plain(live.render(RAYS_BREWERS, LINESCORE, {'abstractGameState': 'Final', 'detailedState': 'Final'}))
    assert 'Final: TB 1 - 2 MIL' in lines
    assert not any('◆' in line or '◇' in line for line in lines)


def test_render_preview_shows_start_time():
    lines = plain(live.render(CUBS_METS, {}, CUBS_METS['status']))
    assert lines[-1] == 'Scheduled - first pitch at 08:08 PM ET'


def test_live_game_polls_until_final(monkeypatch, capsys):
    statuses = iter([LIVE, LIVE, {'abstractGameState': 'Final', 'detailedState': 'Final'}])
    sleeps = []
    monkeypatch.setattr(live, 'get_games', lambda today: GAMES)
    monkeypatch.setattr(live, 'get_status', lambda game_pk: next(statuses))
    monkeypatch.setattr(live, 'get_linescore', lambda game_pk: LINESCORE)
    monkeypatch.setattr(live.time, 'sleep', sleeps.append)

    live.live_game('Rays', interval=1)

    assert sleeps == [live.MIN_INTERVAL, live.MIN_INTERVAL]
    assert 'Final: TB 1 - 2 MIL' in capsys.readouterr().out


def test_live_game_no_match(monkeypatch, capsys):
    monkeypatch.setattr(live, 'get_games', lambda today: GAMES)
    live.live_game('Yankees')
    assert 'No game found today for "Yankees".' in capsys.readouterr().out
