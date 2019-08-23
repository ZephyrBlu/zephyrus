import datetime
import math
import mpyq
from s2protocol import versions
from heapq import merge
import json


# holds basic info about players
class Player:
    def __init__(self, player_id, profile_id, region_id, realm_id, name, race):
        self.player_id = player_id
        self.name = name
        self.race = race
        self.user_id = None
        self.profile_id = profile_id
        self.region_id = region_id
        self.realm_id = realm_id


def convert_time(windows_time):
    unix_epoch_time = math.floor(windows_time/10000000)-11644473600
    replay_datetime = datetime.datetime.fromtimestamp(unix_epoch_time).strftime('%Y-%m-%d %H:%M:%S')
    return replay_datetime


def calc_sq(*, unspent_resources, collection_rate):
    sq = math.ceil(35 * (0.00137 * collection_rate - math.log(unspent_resources if unspent_resources > 0 else 1)) + 240)
    return sq


def get_ids(player_info, events):
    # get player name and race
    # workingSetSlotId correlates to playerIDs
    players = {}

    time_played_at = convert_time(player_info['m_timeUTC'])
    game_map = player_info['m_title'].decode('utf-8')
    metadata = {
        'time_played_at': time_played_at,
        'map': game_map
    }

    # find and record players
    for count, player in enumerate(player_info['m_playerList']):
        if player['m_workingSetSlotId'] is None:
            new_player = Player(
                count,
                player['m_toon']['m_id'],
                player['m_toon']['m_region'],
                player['m_toon']['m_realm'],
                player['m_name'],
                player['m_race']
            )
            players[count] = new_player
        else:   
            new_player = Player(
                player['m_workingSetSlotId'],
                player['m_toon']['m_id'],
                player['m_toon']['m_region'],
                player['m_toon']['m_realm'],
                player['m_name'].decode('utf-8'),
                player['m_race'].decode('utf-8')
            )
            players[player['m_workingSetSlotId']] = new_player

    # first 2 events in every replay with 2 players is always setup for playerIDs
    # need to look at the setup to match player IDs to players
    setup_index = 0
    for setup_index, event in enumerate(events):
        if event['_event'] == 'NNet.Replay.Tracker.SPlayerSetupEvent':
            break

    # logic for translating user_id's into playerID's

    # if only one player then playerID is always 0
    if len (players) == 1:
        player_obj = players[min(players)]
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']
        players[events[setup_index]['m_playerId']] = players.pop(min(players))

    # if both user_id's larger than 2 then lowest user_id first, the largest
    elif min(players) > 2:
        player_obj = players[min(players)]
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']
        players[events[setup_index]['m_playerId']] = players.pop(min(players))

        player_obj = players[max(players)]
        player_obj.player_id = events[setup_index+1]['m_playerId']
        player_obj.user_id = events[setup_index+1]['m_userId']
        players[events[setup_index+1]['m_playerId']] = players.pop(max(players)) 

    # if both user_id's under 2 then the largest is set as 2 and the smallest is set as 1
    # specifically in that order to prevent assignment conflicts
    elif max(players) < 2:
        player_obj = players[max(players)]
        player_obj.player_id = events[setup_index+1]['m_playerId']
        player_obj.user_id = events[setup_index+1]['m_userId']
        players[events[setup_index+1]['m_playerId']] = players.pop(max(players))

        player_obj = players[min(players)]
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']
        players[events[setup_index]['m_playerId']] = players.pop(min(players))

    # else specific numbers don't matter and smallest user_id correlates to playerID of 1
    # and largest user_id correlates to playerID of 2
    # not sure if I need this
    else:
        player_obj = players[min(players)]
        player_obj.player_id = events[setup_index]['m_playerId']
        player_obj.user_id = events[setup_index]['m_userId']
        players[events[setup_index]['m_playerId']] = players.pop(min(players))

        player_obj = players[max(players)]
        player_obj.player_id = events[setup_index+1]['m_playerId']
        player_obj.user_id = events[setup_index+1]['m_userId']
        players[events[setup_index+1]['m_playerId']] = players.pop(max(players))

    return players, metadata


def setup(filename):
    archive = mpyq.MPQArchive(filename)
    
    # getting correct game version and protocol
    contents = archive.header['user_data_header']['content']

    header = versions.latest().decode_replay_header(contents)

    base_build = header['m_version']['m_baseBuild']
    protocol = versions.build(base_build)

    # accessing neccessary parts of file for data
    contents = archive.read_file('replay.tracker.events')
    details = archive.read_file('replay.details')
    gameInfo = archive.read_file('replay.game.events')
    init_data = archive.read_file('replay.initData')

    metadata = json.loads(archive.read_file('replay.gamemetadata.json'))

    # translating data into dict format info
    game_events = protocol.decode_replay_game_events(gameInfo)
    player_info = protocol.decode_replay_details(details)
    tracker_events = protocol.decode_replay_tracker_events(contents)
    detailed_info = protocol.decode_replay_initdata(init_data)

    # all info is returned as generators
    #
    # to paint the full picture of the game
    # both game and tracker events are needed
    # so they are combined then sorted in chronological order

    events = merge(game_events, tracker_events, key=lambda x: x['_gameloop'])
    events = sorted(events, key=lambda x: x['_gameloop'])

    for event in events:
        if event['_event'] == 'NNet.Game.SGameUserLeaveEvent':
            game_length = event['_gameloop']
            break

    return events, player_info, detailed_info, metadata, game_length, protocol


def main(filename):
    try:
        events, player_info, detailed_info, metadata, game_length, protocol = setup(filename)
        players, metadata_export = get_ids(player_info, events)
    except ValueError as error:
        print('A ValueError occured (Unreadable header):', error)
        return None, None, None
    except ImportError as error:
        print('An ImportError occured (Unsupported protocol):', error)
        return None, None, None
    except KeyError as error:
        print('A KeyError error occured (Unreadable file info):', error)
        return None, None, None

    summary_stats = {
        'mmr': {1: 0, 2: 0},
        'mmr_diff': {1: 0, 2: 0},
        'avg_resource_collection_rate': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'avg_unspent_resources': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'apm': {1: 0, 2: 0},
        'resources_lost': {
            'minerals': {1: 0, 2: 0},
            'gas': {1: 0, 2: 0}
        },
        'workers_produced': {1: 0, 2: 0},
        'workers_lost': {1: 0, 2: 0},
        'inject_count': {1: 0, 2: 0},
        'sq': {1: 0, 2: 0}
    }

    metadata_export['game_length'] = math.floor(game_length/22.4)

    mmr_data = detailed_info['m_syncLobbyState']['m_userInitialData']
    if not mmr_data[1]['m_scaledRating'] or mmr_data[2]['m_scaledRating']:
        return None, None, None

    ranked_game = False
    player1_mmr = mmr_data[0]['m_scaledRating']
    player2_mmr = mmr_data[1]['m_scaledRating']
    for p in metadata['Players']: 
        if player1_mmr and player2_mmr:
            ranked_game = True
        else:
            ranked_game = False

        if p['Result'] == 'Win':
            metadata_export['winner'] = p['PlayerID']

    for player in metadata['Players']:
        player_id = player['PlayerID']

        summary_stats['apm'][player_id] = player['APM']

        if mmr_data[player_id-1]['m_scaledRating']:
            summary_stats['mmr'][player_id] = mmr_data[player_id-1]['m_scaledRating']
        else:
            summary_stats['mmr'][player_id] = 0

    if ranked_game:
        summary_stats['mmr_diff'][1] = player1_mmr-player2_mmr
        summary_stats['mmr_diff'][2] = player2_mmr-player1_mmr

    unspent_resources = {
        'minerals': {1: [], 2: []},
        'gas': {1: [], 2: []}
    }

    collection_rate = {
        'minerals': {1: [], 2: []},
        'gas': {1: [], 2: []}
    }

    workers = ['SCV', 'Drone', 'Probe']
    current_ability = {1: None, 2: None}
    for event in events:
        if event['_event'] == 'NNet.Replay.Tracker.SPlayerStatsEvent':
            if event['_gameloop'] != 1:
                unspent_resources['minerals'][event['m_playerId']].append(event['m_stats']['m_scoreValueMineralsCurrent'])
                unspent_resources['gas'][event['m_playerId']].append(event['m_stats']['m_scoreValueVespeneCurrent'])
                
                collection_rate['minerals'][event['m_playerId']].append(event['m_stats']['m_scoreValueMineralsCollectionRate'])
                collection_rate['gas'][event['m_playerId']].append(event['m_stats']['m_scoreValueVespeneCollectionRate'])

            if event['_gameloop'] == game_length:
                summary_stats['resources_lost']['minerals'][event['m_playerId']] = event['m_stats']['m_scoreValueMineralsLostArmy']
                summary_stats['resources_lost']['gas'][event['m_playerId']] = event['m_stats']['m_scoreValueVespeneLostArmy']

                player_minerals = unspent_resources['minerals'][event['m_playerId']]
                player_gas = unspent_resources['gas'][event['m_playerId']]
                summary_stats['avg_unspent_resources']['minerals'][event['m_playerId']] = round(sum(player_minerals)/len(player_minerals), 1)
                summary_stats['avg_unspent_resources']['gas'][event['m_playerId']] = round(sum(player_gas)/len(player_gas), 1)

                player_minerals_collection = collection_rate['minerals'][event['m_playerId']]
                player_gas_collection = collection_rate['gas'][event['m_playerId']]
                summary_stats['avg_resource_collection_rate']['minerals'][event['m_playerId']] = round(sum(player_minerals_collection)/len(player_minerals_collection), 1)
                summary_stats['avg_resource_collection_rate']['gas'][event['m_playerId']] = round(sum(player_gas_collection)/len(player_gas_collection), 1)

                total_collection_rate = summary_stats['avg_resource_collection_rate']['minerals'][event['m_playerId']] + summary_stats['avg_resource_collection_rate']['gas'][event['m_playerId']]
                total_avg_unspent = summary_stats['avg_unspent_resources']['minerals'][event['m_playerId']] + summary_stats['avg_unspent_resources']['gas'][event['m_playerId']]
                player_sq = calc_sq(unspent_resources=total_avg_unspent, collection_rate=total_collection_rate)
                summary_stats['sq'][event['m_playerId']] = player_sq

                current_workers = event['m_stats']['m_scoreValueWorkersActiveCount']
                workers_produced = summary_stats['workers_produced'][event['m_playerId']]
                summary_stats['workers_lost'][event['m_playerId']] = workers_produced + 12 - current_workers


        elif event['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent':
            if event['m_unitTypeName'].decode('utf-8') in workers:
                summary_stats['workers_produced'][event['m_controlPlayerId']] += 1


        elif event['_event'] == 'NNet.Game.SCmdEvent':
            # Spawn Larva, i.e Inject
            if event['m_abil']:
                current_player = None
                for player_id, player in players.items():
                        if player.user_id == event['_userid']['m_userId']:
                            current_player = player

                if event['m_abil']['m_abilLink'] == 183:
                    summary_stats['inject_count'][current_player.player_id] += 1
                current_ability[current_player.player_id] = event['m_abil']['m_abilLink']

        elif event['_event'] == 'NNet.Game.SCommandManagerStateEvent':
            for player_id, player in players.items():
                if player.user_id == event['_userid']['m_userId']:
                    current_player = player

            if current_ability[current_player.player_id] == 183:
                summary_stats['inject_count'][current_player.player_id] += 1

    return players, summary_stats, metadata_export
