from .utils.replay_parser_production import main as replay_parser


def parse_replay(file):
    summary_info = replay_parser(file)
    return summary_info
