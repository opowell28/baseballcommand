import pytest
import requests

from baseballcommand.commands import players


def make_player(player_id, full_name, use_name, last_name, abbreviation, position_type):
    return {
        'id': player_id,
        'fullName': full_name,
        'useName': use_name,
        'lastName': last_name,
        'primaryPosition': {'abbreviation': abbreviation, 'type': position_type},
    }


CROW_ARMSTRONG = make_player(691718, 'Pete Crow-Armstrong', 'Pete', 'Crow-Armstrong', 'CF', 'Outfielder')
ALONSO = make_player(624413, 'Pete Alonso', 'Pete', 'Alonso', '1B', 'Infielder')
ACUNA = make_player(660670, 'Ronald Acuña Jr.', 'Ronald', 'Acuña', 'RF', 'Outfielder')
GARCIA_JR = make_player(671277, 'Luis García Jr.', 'Luis', 'García', '1B', 'Infielder')
GARCIA_P = make_player(472610, 'Luis García', 'Luis', 'García', 'P', 'Pitcher')
OHTANI = make_player(660271, 'Shohei Ohtani', 'Shohei', 'Ohtani', 'TWP', 'Two-Way Player')
KING = make_player(650633, 'Michael King', 'Mike', 'King', 'P', 'Pitcher')

PLAYERS = [CROW_ARMSTRONG, ALONSO, ACUNA, GARCIA_JR, GARCIA_P, OHTANI, KING]


class FakeResponse:
    def __init__(self, data, status_code=200):
        self.data = data
        self.status_code = status_code

    def json(self):
        return self.data

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.HTTPError(f'{self.status_code} Error')


@pytest.fixture
def fake_api(monkeypatch):
    # Serves the player list and per-group stats without hitting the MLB API
    requested_urls = []
    stats = {'hitting': {'gamesPlayed': 162, 'avg': '.280'}, 'pitching': {'gamesPitched': 14, 'era': '1.79'}}

    def fake_get(url):
        requested_urls.append(url)
        if '/sports/1/players' in url:
            return FakeResponse({'people': PLAYERS})
        group = 'pitching' if 'group=pitching' in url else 'hitting'
        return FakeResponse({'stats': [{'splits': [{'stat': stats[group], 'team': {'id': 1}}]}]})

    monkeypatch.setattr(players.requests, 'get', fake_get)
    return requested_urls


@pytest.mark.parametrize('name, expected', [
    ('Ronald Acuña Jr.', 'ronald acuna'),
    ('Pete Crow-Armstrong', 'pete crow armstrong'),
    ('  PETE   ALONSO ', 'pete alonso'),
    ("Travis d'Arnaud", 'travis darnaud'),
    ('Ken Griffey III', 'ken griffey'),
])
def test_normalize_name(name, expected):
    assert players.normalize_name(name) == expected


@pytest.mark.parametrize('name, expected', [
    ('Pete Crow-Armstrong', CROW_ARMSTRONG),
    ('pete crow armstrong', CROW_ARMSTRONG),
    ('Pete Alonso', ALONSO),
    ('Ronald Acuna', ACUNA),
    ('ronald acuña jr', ACUNA),
    ('Mike King', KING),
    ('Michael King', KING),
])
def test_find_players_exact_match(name, expected):
    assert players.find_players(name, PLAYERS) == [expected]


def test_find_players_close_match_returns_correct_player():
    # Misspelled last name must not fall back to another player with the same first name
    assert players.find_players('Pete Crowe-Armstrong', PLAYERS) == [CROW_ARMSTRONG]


def test_find_players_returns_all_players_sharing_a_name():
    assert players.find_players('Luis Garcia', PLAYERS) == [GARCIA_JR, GARCIA_P]


def test_find_players_no_match():
    assert players.find_players('Zzz Qqq', PLAYERS) == []


def test_choose_player_valid_choice(monkeypatch):
    monkeypatch.setattr('builtins.input', lambda _: '2')
    assert players.choose_player([GARCIA_JR, GARCIA_P]) == GARCIA_P


@pytest.mark.parametrize('choice', ['0', '3', 'abc'])
def test_choose_player_invalid_choice(monkeypatch, choice):
    monkeypatch.setattr('builtins.input', lambda _: choice)
    assert players.choose_player([GARCIA_JR, GARCIA_P]) is None


def test_get_season_stats_prefers_combined_split_for_traded_player(monkeypatch):
    splits = [
        {'stat': {'hits': 50}, 'team': {'id': 1}},
        {'stat': {'hits': 40}, 'team': {'id': 2}},
        {'stat': {'hits': 90}},
    ]
    monkeypatch.setattr(players.requests, 'get', lambda url: FakeResponse({'stats': [{'splits': splits}]}))
    assert players.get_season_stats(1, 'hitting', 2026) == {'hits': 90}


def test_get_season_stats_no_stats(monkeypatch):
    monkeypatch.setattr(players.requests, 'get', lambda url: FakeResponse({'stats': []}))
    assert players.get_season_stats(1, 'hitting', 2026) is None


@pytest.mark.parametrize('first_name, last_name, expected_groups', [
    ('Pete', 'Alonso', ['hitting']),
    ('Mike', 'King', ['pitching']),
    ('Shohei', 'Ohtani', ['hitting', 'pitching']),
])
def test_player_search_requests_stats_for_position(fake_api, first_name, last_name, expected_groups):
    players.player_search(first_name, last_name)

    stats_urls = [url for url in fake_api if '/stats?' in url]
    assert [url.split('group=')[1].split('&')[0] for url in stats_urls] == expected_groups


def test_player_search_prints_stats(fake_api, capsys):
    players.player_search('Pete', 'Crow-Armstrong')

    out = capsys.readouterr().out
    assert 'Pete Crow-Armstrong (CF)' in out
    assert '162' in out
    assert '.280' in out


def test_player_search_reports_corrected_name(fake_api, capsys):
    players.player_search('Pete', 'Crowe-Armstrong')
    assert 'Showing results for Pete Crow-Armstrong' in capsys.readouterr().out


@pytest.mark.parametrize('first_name, last_name', [('Mike', 'King'), ('Ronald', 'Acuna')])
def test_player_search_exact_match_does_not_report_correction(fake_api, capsys, first_name, last_name):
    players.player_search(first_name, last_name)
    assert 'Showing results for' not in capsys.readouterr().out


def test_player_search_no_match(fake_api, capsys):
    players.player_search('Zzz', 'Qqq')
    assert 'No active MLB player found matching "Zzz Qqq"' in capsys.readouterr().out


def test_player_search_api_error(monkeypatch, capsys):
    monkeypatch.setattr(players.requests, 'get', lambda url: FakeResponse({}, status_code=500))
    players.player_search('Pete', 'Alonso')
    assert 'Error searching for player' in capsys.readouterr().out
