from .utils.mvp import main as replay_parser


async def parse_replay(file):
    parsed_file = await replay_parser(file)
    return parsed_file
