from .mpyq import *
import copy
from .s2protocol_py3 import versions
from heapq import merge

# dict of all possible game objects
# stores stats on all objects
# i.e no. of obj created/dead/alive, supply
gameObjects = {
				'Protoss':
						{'Nexus': [('building', 50), {'live': 0, 'died': 0, 'created': 0}, 15],
						'Pylon': ['building', {'live': 0, 'died': 0, 'created': 0}, 8],
						'Assimilator': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Gateway': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'WarpGate': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Forge': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'CyberneticsCore': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'PhotonCannon': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'ShieldBattery': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'RoboticsFacility': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Stargate': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'TwilightCouncil': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'RoboticsBay': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'FleetBeacon': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'TemplarArchive': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'DarkShrine': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Probe': ['unit', {'live': 0, 'died': 0, 'created': 0}, 1],
						'Zealot': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Stalker': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Sentry': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 2],
						'Adept': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'HighTemplar': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 2],
						'DarkTemplar': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Archon': ['unit', {'live': 0, 'died': 0, 'created': 0}, 4],
						'Observer': ['unit', {'live': 0, 'died': 0, 'created': 0}, 1],
						'WarpPrism': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'WarpPrismPhasing': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Immortal': ['unit', {'live': 0, 'died': 0, 'created': 0}, 4],
						'Colossus': ['unit', {'live': 0, 'died': 0, 'created': 0}, 6],
						'Disruptor': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'Phoenix': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 2],
						'VoidRay': ['unit', {'live': 0, 'died': 0, 'created': 0}, 4],
						'Oracle': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 3],
						'Tempest': ['unit', {'live': 0, 'died': 0, 'created': 0}, 5],
						'Carrier': ['unit', {'live': 0, 'died': 0, 'created': 0}, 6],
						'Interceptor': ['unit', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Mothership': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 8],
						'StasisWard': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'AdeptPhaseShift': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'ForceField': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'OracleStasisTrap': ['building', {'live': 0, 'died': 0, 'created': 0}, 0]},

				'Terran': 
						{'CommandCenter': [('building', 50), {'live': 0, 'died': 0, 'created': 0}, 15],
						'OrbitalCommand': ['building', {'live': 0, 'died': 0, 'created': 0}, 15],
						'PlanetaryFortress': ['building', {'live': 0, 'died': 0, 'created': 0}, 15],
						'SupplyDepot': ['building', {'live': 0, 'died': 0, 'created': 0}, 8],
						'SupplyDepotLowered': ['building', {'live': 0, 'died': 0, 'created': 0}, 8],
						'Refinery': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Barracks': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'EngineeringBay': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Bunker': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'MissileTurret': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'SensorTower': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'GhostAcademy': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Factory': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Starport': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Armory': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'FusionCore': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'BarracksTechLab': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'BarracksReactor': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'StarportTechLab': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'StarportReactor': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'FactoryTechLab': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'FactoryReactor': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'SCV': ['unit', {'live': 0, 'died': 0, 'created': 0}, 1],
						'Marine': ['unit', {'live': 0, 'died': 0, 'created': 0}, 1],
						'Reaper': ['unit', {'live': 0, 'died': 0, 'created': 0}, 1],
						'Marauder': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Ghost': [('unit', 75), {'live': 0, 'died': 0, 'created': 0}, 2],
						'Hellion': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Hellbat': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'WidowMine': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Cyclone': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'SiegeTank': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'SiegeTankSieged': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'Thor': ['unit', {'live': 0, 'died': 0, 'created': 0}, 6],
						'Viking': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Medivac': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 2],
						'Liberator': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'LiberatorAG': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'Raven': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 2],
						'Banshee': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 3],
						'Battlecruiser': ['unit', {'live': 0, 'died': 0, 'created': 0}, 6],
						'MULE': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'AutoTurret': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'OracleStasisTrap': ['building', {'live': 0, 'died': 0, 'created': 0}, 0]},

				'Zerg':
						{'Hatchery': ['building', {'live': 0, 'died': 0, 'created': 0}, 15],
						'Extractor': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'SpawningPool': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'SpineCrawler': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'SporeCrawler': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'EvolutionChamber': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'RoachWarren': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'BanelingNest': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Lair': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'HydraliskDen': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'LurkerDenMP': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Spire': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'GreaterSpire': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'NydusNetwork': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'NydusWorm': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'NydusCanal': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'InfestationPit': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Hive': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'UltraliskCavern': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'CreepTumor': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'CreepTumorBurrowed': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'CreepTumorQueen': ['building', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Larva': ['unit', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Cocoon': ['unit', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Drone': ['unit', {'live': 0, 'died': 0, 'created': 0}, 1],
						'Overlord': ['building', {'live': 0, 'died': 0, 'created': 0}, 8], # special consideration
						'Queen': [('unit', 25), {'live': 0, 'died': 0, 'created': 0}, 2],
						'Zergling': ['unit', {'live': 0, 'died': 0, 'created': 0}, 0.5],
						'Baneling': ['unit', {'live': 0, 'died': 0, 'created': 0}, 0.5],
						'Roach': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Ravager': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'Overseer': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 0],
						'Hydralisk': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'LurkerMP': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'Mutalisk': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'Corruptor': ['unit', {'live': 0, 'died': 0, 'created': 0}, 2],
						'SwarmHostMP': ['unit', {'live': 0, 'died': 0, 'created': 0}, 3],
						'Infestor': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 2],
						'Viper': [('unit', 50), {'live': 0, 'died': 0, 'created': 0}, 3],
						'BroodLord': ['unit', {'live': 0, 'died': 0, 'created': 0}, 4],
						'Ultralisk': ['unit', {'live': 0, 'died': 0, 'created': 0}, 6],
						'Changeling': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'ChangelingZealot': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'ChangelingZergling': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'ChangelingMarine': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'InfestedTerran': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'LocustMPPrecursor': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'LocustMP': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'LocustMPFlying': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Broodling': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'Egg': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'BanelingCocoon': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'RavagerCocoon': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'LurkerMPEgg': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'BroodLordCocoon': ['temporary', {'live': 0, 'died': 0, 'created': 0}, 0],
						'OracleStasisTrap': ['building', {'live': 0, 'died': 0, 'created': 0}, 0]}
				}


# stores basic info about each player
# i.e name, race, id

nonEnglishRaces = {b'\xed\x94\x84\xeb\xa1\x9c\xed\x86\xa0\xec\x8a\xa4': 'Protoss',
											'\xe6\x98\x9f\xe7\x81\xb5': 'Protoss',
											'\xe7\xa5\x9e\xe6\x97\x8f': 'Protoss',
	b'\xd0\x9f\xd1\x80\xd0\xbe\xd1\x82\xd0\xbe\xd1\x81\xd1\x81\xd1\x8b': 'Protoss',
											b'\xec\xa0\x80\xea\xb7\xb8': 'Zerg',
											b'\xe5\xbc\x82\xe8\x99\xab': 'Zerg',
											b'\xe8\x9f\xb2\xe6\x97\x8f': 'Zerg',
											b'\xed\x85\x8c\xeb\x9e\x80': 'Terran',
											b'\xe4\xba\xba\xe9\xa1\x9e': 'Terran',
			b'\xd0\xa2\xd0\xb5\xd1\x80\xd1\x80\xd0\xb0\xd0\xbd\xd1\x8b': 'Terran',
											b'\xe4\xba\xba\xe7\xb1\xbb': 'Terran'}

objInProgress = []
objInfo = []
players = {}
gameLength = 0


# holds basic info about players and also supply
class Player:
	def __init__(self, playerID, name, race):
		self.playerID = playerID
		self.name = name
		self.race = race
		self.supply = {'active': 0, 'cap': 0}
		self.objects = None
		self.userID = None
		self.win = None
		self.minerals = []
		self.gas = []
		self.mineralCol = []
		self.gasCol = []

	def updateSupply(self):
		for obj in objInfo:
			if obj.deathTime == None and obj.player.playerID == self.playerID:
				if obj.type == 'unit':
					self.supply['active'] += self.objects[obj.name][2]
				elif obj.type == 'building':
					self.supply['cap'] += self.objects[obj.name][2]
					if self.supply['cap'] > 200:
						self.supply['cap'] = 200
				else:
					continue
			else:
				continue


# format for every object instanced in game
class GameObj:
	def __init__(self, player, objID, name, birthTime, status='completed'):
		self.player = player
		self.objID = objID
		self.name = name
		self.birthTime = birthTime
		self.status = status
		self.type = None
		self.energy = None
		self.deathTime = None
		self.identify()

	# finds object type
	# i.e unit, building, temporary
	def identify(self):
		obj = self.player.objects[self.name][0]
		if type(obj) == tuple:
			self.type = obj[0]
			self.energy = obj[1]
		else:
			self.type = obj

	# currently redundant functions
	def updateEnergy(self, ticks):
		self.energy += ticks

	def timeAlive(self):
		if deathTime != None:
			return deathTime - birthTime
		else:
			return None


def getObj(objID, objList):
	for gameObj in objList:
		if gameObj.objID == objID:
			return gameObj


def getIDs(playerInfo, events):
	# get player name and race
	# workingSetSlotId correlates to playerIDs
	players.clear()
	for count, player in enumerate(playerInfo['m_playerList']):
		if player['m_workingSetSlotId'] is None:
			newPlayer = Player(count, player['m_name'], player['m_race'])
			players[count] = newPlayer
		else:	
			newPlayer = Player(player['m_workingSetSlotId'], player['m_name'], player['m_race'])
			players[player['m_workingSetSlotId']] = newPlayer

	for key, player in players.items():
		if player.race != 'Protoss' and player.race != 'Zerg' and player.race != 'Terran':
			player.race = nonEnglishRaces[player.race]
		player.objects = copy.deepcopy(gameObjects[player.race])

	# first 2 events in every replay with 2 players is always setup for playerIDs
	# need to look at the setup to match player IDs to players

	setupIndex = 0
	for setupIndex, event in enumerate(events):
		if event['_event'] == 'NNet.Replay.Tracker.SPlayerSetupEvent':
			break

	if len (players) == 1:
		playerObj = players[min(players)]
		playerObj.playerID = events[setupIndex]['m_playerId']
		playerObj.userID = events[setupIndex]['m_userId']
		players[events[setupIndex]['m_playerId']] = players.pop(min(players))

	elif min(players) > 2:
		playerObj = players[min(players)]
		playerObj.playerID = events[setupIndex]['m_playerId']
		playerObj.userID = events[setupIndex]['m_userId']
		players[events[setupIndex]['m_playerId']] = players.pop(min(players))

		playerObj = players[max(players)]
		playerObj.playerID = events[setupIndex+1]['m_playerId']
		playerObj.userID = events[setupIndex+1]['m_userId']
		players[events[setupIndex+1]['m_playerId']] = players.pop(max(players))	

	elif max(players) < 2:
		playerObj = players[max(players)]
		playerObj.playerID = events[setupIndex+1]['m_playerId']
		playerObj.userID = events[setupIndex+1]['m_userId']
		players[events[setupIndex+1]['m_playerId']] = players.pop(max(players))

		playerObj = players[min(players)]
		playerObj.playerID = events[setupIndex]['m_playerId']
		playerObj.userID = events[setupIndex]['m_userId']
		players[events[setupIndex]['m_playerId']] = players.pop(min(players))

	else:
		playerObj = players[min(players)]
		playerObj.playerID = events[setupIndex]['m_playerId']
		playerObj.userID = events[setupIndex]['m_userId']
		players[events[setupIndex]['m_playerId']] = players.pop(min(players))

		playerObj = players[max(players)]
		playerObj.playerID = events[setupIndex+1]['m_playerId']
		playerObj.userID = events[setupIndex+1]['m_userId']
		players[events[setupIndex+1]['m_playerId']] = players.pop(max(players))
	return players

# setting up game version stuff
# extracting base level data from replay file
#
# tracker events are human readable data about the game, quite limited though
# game events are what the engine uses to recreate the game, a lot more info
# details is setup info for the lobby


def setup(filename):
	archive = MPQArchive(filename)
	
	# getting correct game version and protocol
	contents = archive.header['user_data_header']['content']

	header = versions.latest().decode_replay_header(contents)

	baseBuild = header['m_version']['m_baseBuild']
	protocol = versions.build(baseBuild)

	# accessing neccessary parts of file for data
	contents = archive.read_file('replay.tracker.events')
	details = archive.read_file('replay.details')
	gameInfo = archive.read_file('replay.game.events')

	# translating data into dict format info
	gameEvents = protocol.decode_replay_game_events(gameInfo)
	playerInfo = protocol.decode_replay_details(details)
	trackerEvents = protocol.decode_replay_tracker_events(contents)

	# all info is returned as generators
	#
	# to paint the full picture of the game
	# both game and tracker events are needed
	# so they are combined then sorted in chronological order
	events = merge(gameEvents, trackerEvents, key=lambda x: x['_gameloop'])
	events = sorted(events, key=lambda x: x['_gameloop'])

	return events, playerInfo


def main(filename):
	objInProgress = []
	objInfo = []
	players = {}
	injectTimes = []

	global errorReplay
	errorReplay = 0

	try:
		events, playerInfo = setup(filename)
		players = getIDs(playerInfo, events)
	# KeyError for unreadable file info
	# ValueError for unreadable header
	# Import error for unsupported protocol
	except (ValueError, ImportError, KeyError) as error:
		errorReplay += 1
		return error, errorReplay

	for count, event in enumerate(events):
		# --------------------TO DO---------------------
		# - create dict of possible events instead of elif

		# try-except is to deal with general issues of events
		# not containing specific information
		# especially objects initialized @ time=0
		try:
			if event['_event'] == 'NNet.Game.SCmdEvent':
				# most m_abil's are None type
				# so need TypeError execption to bypass
				# SCmdEvent's not relevant to injects
				try:
					activeAbil = event['m_abil']['m_abilLink']
					# need to create library of ability #'s
					# 111 = inject, found by combing through game events
					if activeAbil == 111:
						injectTimes.append(event['_gameloop'])
					elif activeAbil == 176:
						stormsCast += 1
					elif activeAbil == 245:
						transfuses += 1
					else:
						activeAbil = None
				except TypeError:
					activeAbil = None
					continue

			# event for spell being cast on building
			# occurs when multiple spells are cast in quick succession
			# again found through trial and error
			# elif event['_event'] == 'NNet.Game.SCmdUpdateTargetUnitEvent':
			# 	if event['m_target']['m_snapshotUnitLink'] == 108:
			# 		injectTimes.append(event['_gameloop'])

			# unitInit events occur during warp ins, morphing and creating structures
			# units in production do not create this type of event
			elif event['_event'] == 'NNet.Replay.Tracker.SUnitInitEvent':
				eventObj = GameObj(players[event['m_controlPlayerId']], event['m_unitTagIndex'], event['m_unitTypeName'].decode('utf-8'), None, 'building')
				objInProgress.append(eventObj)
				players[event['m_controlPlayerId']].objects[event['m_unitTypeName']][1]['live'] += 1
				players[event['m_controlPlayerId']].objects[event['m_unitTypeName']][1]['created'] += 1
				if eventObj.player.race == 'Protoss' and eventObj.type == 'unit':
					global warpIns
					warpIns += 1
				
			# unitDone events occur only after a corresponding unitInit event
			elif event['_event'] == 'NNet.Replay.Tracker.SUnitDoneEvent':
				eventObj = getObj(event['m_unitTagIndex'], objInProgress)
				eventObj.birthTime = event['_gameloop']
				eventObj.status = 'completed'
				objInfo.append(eventObj)
				objInProgress.remove(eventObj)

			# unitBorn events occur for units being produced from structures
			# also occurs for larva spawns
			elif event['_event'] == 'NNet.Replay.Tracker.SUnitBornEvent':
				eventObj = GameObj(players[event['m_controlPlayerId']], event['m_unitTagIndex'], event['m_unitTypeName'].decode('utf-8'), event['_gameloop'])
				objInfo.append(eventObj)
				players[event['m_controlPlayerId']].objects[event['m_unitTypeName']][1]['live'] += 1
				players[event['m_controlPlayerId']].objects[event['m_unitTypeName']][1]['created'] += 1

			# unitDied events occur when any unit or structure is killed/destroyed
			#
			# creep tumors have weird interactions with this event
			# they go from unitInit state to unitDied state
			# and then also go through a typeChange
			elif event['_event'] == 'NNet.Replay.Tracker.SUnitDiedEvent':
				#print(event)
				# try-except is to deal with mineral field objects and other
				# things intialized at the start of the game that I don't care about
				# unitDied events occur in them when minerals/gas are depleted, rocks destroyed, etc
				try:
					# creep tumors are an edge case. They go from unitInit state to unitDied state. Annoying
					if getObj(event['m_unitTagIndex'], objInProgress) != None and 'CreepTumor' in getObj(event['m_unitTagIndex'], objInProgress).name:
						objInProgress.remove(getObj(event['m_unitTagIndex'], objInProgress))
					else:
						eventObj = getObj(event['m_unitTagIndex'], objInfo)
						# if obj was not killed by another obj then it hasn't 'died'
						if event['m_killerUnitTagIndex'] != None:
							getObj(event['m_unitTagIndex'], objInfo).player.objects[eventObj.name][1]['died'] += 1
							if eventObj.name == 'Drone' and getObj(event['m_killerUnitTagIndex'], objInfo).name == 'Oracle':
								dronesKilled += 1
								killTimes.append(event['_gameloop'])
						getObj(event['m_unitTagIndex'], objInfo).player.objects[eventObj.name][1]['live'] -= 1
						eventObj.deathTime = event['_gameloop']
						eventObj.objID = None
				except AttributeError:
					continue

			# typeChange events occur when a unit/building is altered
			# but unitTagIndex and recycleTag are unchanged
			# i.e morphing, larva -> egg
			elif event['_event'] == 'NNet.Replay.Tracker.SUnitTypeChangeEvent':
				# try-except is to deal with mineral field objects and other
				# things intialized at the start of the game that I don't care about
				# typeChange events occurs in them when minerals are reduced
				try:
					eventObj = getObj(event['m_unitTagIndex'], objInfo) # find old object
					getObj(event['m_unitTagIndex'], objInfo).player.objects[eventObj.name][1]['live'] -= 1 # update old object type
					getObj(event['m_unitTagIndex'], objInfo).player.objects[event['m_unitTypeName']][1]['live'] += 1 # update new object type
					getObj(event['m_unitTagIndex'], objInfo).player.objects[event['m_unitTypeName']][1]['created'] += 1 # update new object type
					eventObj.name = event['m_unitTypeName'].decode('utf-8') #update old object
				except AttributeError:
					continue
			elif event['_event'] == 'NNet.Game.SGameUserLeaveEvent':
				global gameLength
				gameLength = event['_gameloop']
				for k, player in players.items():
					if player.userID == event['_userid']['m_userId']:
						player.win = 0
					else:
						player.win = 1
		except KeyError:
			continue
	return gameLength, errorReplay
