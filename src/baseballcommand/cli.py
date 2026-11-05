import argparse

from .commands import live, players, schedule


def cli() -> None:
    parser = argparse.ArgumentParser(prog='BaseballCommand')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('leagues', help='Return a list of MLB leagues.')
    subparsers.add_parser('schedule', help='Return a list of todays games.')

    player_parser = subparsers.add_parser('player', help='Return stats for the specified player for the current season.')
    player_parser.add_argument('first_name')
    player_parser.add_argument('last_name')

    live_parser = subparsers.add_parser('live', help='Watch a live game with the score and runners on base.')
    live_parser.add_argument('team', nargs='?', help='Team name or abbreviation, e.g. "Cubs" or "NYY".')
    live_parser.add_argument('--interval', type=int, default=live.MIN_INTERVAL,
                             help=f'Seconds between updates (minimum {live.MIN_INTERVAL}).')
    live_parser.add_argument('--once', action='store_true', help='Show the game once instead of refreshing.')

    args = parser.parse_args()

    if args.command == 'live':
        live.live_game(args.team, args.interval, args.once)
    elif args.command == 'player':
        players.player_search(f'{args.first_name}', f'{args.last_name}')
    elif args.command == 'leagues':
        schedule.get_leagues()
    elif args.command == 'schedule':
        schedule.get_todays_schedule()