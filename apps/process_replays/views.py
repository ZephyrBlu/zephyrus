from .utils.mvp import main as replay_parser


def parse_replay(file):
    parsed_file = replay_parser(file)
    return parsed_file
