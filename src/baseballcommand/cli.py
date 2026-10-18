import argparse

from .commands import schedule, players


def cli() -> None:
    parser = argparse.ArgumentParser(prog='BaseballCommand')
    subparsers = parser.add_subparsers(dest='command', required=True)

    subparsers.add_parser('leagues', help='Return a list of MLB leagues.')
    subparsers.add_parser('schedule', help='Return a list of todays games.')

    player_parser = subparsers.add_parser('player', help='Return stats for the specified player for the current season.')
    player_parser.add_argument('first_name')
    player_parser.add_argument('last_name')

    args = parser.parse_args()

    if args.command == 'player':
        players.player_search(f'{args.first_name}', f'{args.last_name}')
    elif args.command == 'leagues':
        schedule.get_leagues()
    elif args.command == 'schedule':
        schedule.get_todays_schedule()