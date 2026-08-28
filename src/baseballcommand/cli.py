import argparse

from . import commands


def cli() -> None:
    # List all possible functions here
    FUNCTION_MAP = {
        'leagues': commands.get_leagues,
        'schedule': commands.get_todays_schedule
    }

    parser = argparse.ArgumentParser(
        prog='BaseballCommand',
        description="Get scores and stats from around the MLB."
    )

    parser.add_argument('command', choices=FUNCTION_MAP.keys())

    args = parser.parse_args()

    func = FUNCTION_MAP[args.command]
    func()
