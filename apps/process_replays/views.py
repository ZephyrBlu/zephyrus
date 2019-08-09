from .utils.mvp import main as replay_parser


def parse_replay(file):
    players, summary_stats, metadata = replay_parser(file)
    return players, summary_stats, metadata
