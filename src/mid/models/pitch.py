PITCH_LENGTH = 120.0
PITCH_WIDTH = 80.0


def attack_direction(team: str, period: int | None = 1) -> int:
    """
    Handy auxiliary function to determine the attack direction of a team, +1 if 
    towards 120, -1 if towards 0. Sides swap at half-time (Represented as 'period')

    Args:
        team (str): The team name.
        period (int): The period of the match.

    Returns:
        int: The attack direction of the team.
    """
    base = 1 if team == "home" else -1
    return -base if period == 2 else base
