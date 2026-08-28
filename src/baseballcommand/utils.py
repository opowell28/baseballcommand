from datetime import datetime
from zoneinfo import ZoneInfo


def UTC_to_EST(UTC_time):
    dt = datetime.fromisoformat(UTC_time)
    # Convert UTC to US Eastern time
    eastern_dt = dt.astimezone(ZoneInfo('America/New_York'))
    # Isolate just the time (game_date contains full date and time)
    return eastern_dt.strftime('%I:%M %p')