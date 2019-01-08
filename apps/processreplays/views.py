from .utils.replay_parser_production import main as replay_parser


def parse_replay(file):
    gameLength, errors = replay_parser(file)
    return gameLength
