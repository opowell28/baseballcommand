import argparse

from . import commands
from .commands import schedule


def cli() -> None:
    # List all possible functions here
    FUNCTION_MAP = {
        'leagues': schedule.get_leagues,
        'schedule': schedule.get_todays_schedule
    }

    parser = argparse.ArgumentParser(
        prog='BaseballCommand',
        description="Get scores and stats from around the MLB."
    )

    parser.add_argument('command', choices=FUNCTION_MAP.keys())

    args = parser.parse_args()

    func = FUNCTION_MAP[args.command]
    func()
