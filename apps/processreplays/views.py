from .utils.replay_parser_production import main as replay_parser


def parse_replay(file):
    errors, meta_data, player_info, summary_info = replay_parser(file)
    return errors, meta_data, player_info, summary_info
