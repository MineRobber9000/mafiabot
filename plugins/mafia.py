import dictdata, random
from bot import IRCLine
BOT = None

def PRIVMSG(target,msg):
	if not BOT: return
	BOT.socket.send(IRCLine("PRIVMSG",target,msg).line)

def respond(event,message,force_no_prefix=False):
	prefix = ""
	target = event.target
	if target.startswith("#"):
		prefix = event.hostmask.nick+": " if not force_no_prefix else ""
	else:
		target = event.hostmask.nick
	PRIVMSG(target,prefix+message)

from enum import IntEnum, auto
class GameState(IntEnum):
	NO_GAME=auto()
	WAITING_FOR_FOUR=auto()
	MAFIA=auto()
	DOCTOR=auto()
	SHERIFF=auto()

GAME = dict(mafia=None,doctor=None,sheriff=None,townspeople=[],state=GameState.NO_GAME,mafia_chose=None,doctor_chose=None,sheriff_chose=None,doctor_dead=False)
CHANNEL = "#mafia"

# Strings
JOINED = "Joined!"
NEW_GAME = "A NEW GAME OF MAFIA IS BEGINNING! TYPE `!join` TO JOIN!"
MINIMUM_REACHED = "The minimum number of players has been reached, type `!start` to start"
ALREADY_JOINED = "You have already joined the game!"
GAME_IN_PROGRESS = "A game is currently in progress; please wait for this game to finish."
NO_OPEN_GAME = "There isn't an open game. Start one by typing `!join`."
NOT_ENOUGH_TO_START = "There aren't enough players to start the game yet. ({!s} < 4)"
ROLE_MSG = "Your role for this game is: {}"
ROLES_CHOSEN = "Everybody has been sent their role for the game, and we shall begin."
MAFIA_PUB="First, the mafia chooses their target..."
MAFIA_PRIV="Respond with the nick of the user you wish to target."
DOCTOR_PUB="...then, the doctor chooses who to save..."
DOCTOR_PRIV="Respond with the nick of the user you wish to save."
SHERIFF_PUB="...and finally, the sheriff chooses who they believe the mafia member to be."
SHERIFF_PRIV="Respond with the nick of the user you believe to be the mafia."
CANT_CHOOSE_SELF="You can't choose *yourself*, that's not how this game works!"
INVALID_TARGET="That user isn't in the game!"
LIST_TARGETS="The players are: {}"
END_MSG_1="{} was targeted by the mafia and {}."
WAS_THE_SHERIFF="{}, the sheriff,"
WAS_THE_DOCTOR="{}, the doctor,"
TARGET_SAVED="was saved"
TARGET_DIED="died"
END_MSG_2A="The sheriff hanged {} on suspicions of them being the mafia. These suspicions proved to be {{}}."
TARGET_CORRECT="correct, and the town was saved"
TARGET_INCORRECT="wrong"
END_MSG_2B="The sheriff's dying words implicated {} as having been the mafia, and they were hanged by the town in mob justice."
END_2B_CORRECT="The sheriff had been correct, and the town was saved."
END_2B_INCORRECT="The sheriff had been wrong, and the mafia took over the town."
END_MSG_2C="The sheriff had believed {} to have been the mafia, but those suspicions were clearly proven incorrect."
ROUND_OVER="This ends this game of mafia."

def on_command_join(event):
	global GAME
	if not event.target.startswith("#"): return None
	if event.hostmask.nick in GAME["townspeople"] or any([x==event.hostmask.nick for x in [GAME[y] for y in "mafia doctor sheriff".split()]]):
		respond(event,ALREADY_JOINED)
		return
	if GAME["state"]==GameState.NO_GAME:
		GAME["state"]=GameState.WAITING_FOR_FOUR
		GAME["townspeople"].append(event.hostmask.nick)
		respond(event,JOINED)
		respond(event,NEW_GAME,True)
	elif GAME["state"]==GameState.WAITING_FOR_FOUR:
		GAME["townspeople"].append(event.hostmask.nick)
		respond(event,JOINED)
		if len(GAME["townspeople"])>=4:
			respond(event,MINIMUM_REACHED,True)
	else:
		respond(event,GAME_IN_PROGRESS)

def on_command_start(event):
	global GAME
	if GAME["state"]!=GameState.WAITING_FOR_FOUR:
		if GAME["state"]==GameState.NO_GAME:
			respond(event,NO_OPEN_GAME)
			return
		else:
			respond(event,GAME_IN_PROGRESS)
			return
	if len(GAME["townspeople"])<4:
		respond(event,NOT_ENOUGH_TO_START.format(len(GAME["townspeople"])))
		return
	mafia, doctor, sheriff = random.sample(GAME["townspeople"],3)
	GAME["townspeople"].remove(mafia)
	GAME["mafia"]=mafia
	GAME["townspeople"].remove(doctor)
	GAME["doctor"]=doctor
	GAME["townspeople"].remove(sheriff)
	GAME["sheriff"]=sheriff
	PRIVMSG(mafia,ROLE_MSG.format("mafia"))
	PRIVMSG(doctor,ROLE_MSG.format("doctor"))
	PRIVMSG(sheriff,ROLE_MSG.format("sheriff"))
	for person in GAME["townspeople"]:
		PRIVMSG(person,ROLE_MSG.format("townsperson"))
	respond(event,ROLES_CHOSEN)
	targets = [GAME[x] for x in "mafia doctor sheriff".split()]+GAME["townspeople"]
	random.shuffle(targets)
	respond(event,LIST_TARGETS.format(",".format(targets)))
	respond(event,MAFIA_PUB,True)
	PRIVMSG(mafia,MAFIA_PRIV)
	GAME["state"]=GameState.MAFIA

def on_privmsg(event):
	global GAME, CHANNEL
	if event.target!="mafiabot": return
	targets = [GAME[x] for x in "mafia doctor sheriff".split()]+GAME["townspeople"]
	if GAME["doctor_dead"]: targets.remove(GAME["doctor"])
	random.shuffle(targets)
	if GAME["state"]==GameState.MAFIA and event.hostmask.nick==GAME["mafia"]:
		if event.message in targets:
			if event.message==GAME["mafia"]:
				respond(event,CANT_CHOOSE_SELF)
				return
			GAME["mafia_chose"]=event.message
			if not GAME["doctor_dead"]:
				GAME["state"]=GameState.DOCTOR
				PRIVMSG(CHANNEL,DOCTOR_PUB)
				PRIVMSG(GAME["doctor"],DOCTOR_PRIV)
			else:
				GAME["doctor_chose"]=""
				GAME["state"]=GameState.SHERIFF
				PRIVMSG(CHANNEL,SHERIFF_PUB)
				PRIVMSG(GAME["sheriff"],SHERIFF_PRIV)
		else:
			respond(event,INVALID_TARGET)
			respond(event,LIST_TARGETS.format(", ".join(targets)))
	elif GAME["state"]==GameState.DOCTOR and event.hostmask.nick==GAME["doctor"]:
		if event.message in targets:
			GAME["doctor_chose"]=event.message
			GAME["state"]=GameState.SHERIFF
			PRIVMSG(CHANNEL,SHERIFF_PUB)
			PRIVMSG(GAME["sheriff"],SHERIFF_PRIV)
		else:
			respond(event,INVALID_TARGET)
			respond(event,LIST_TARGETS.format(", ".join(targets)))
	elif GAME["state"]==GameState.SHERIFF and event.hostmask.nick==GAME["sheriff"]:
		if event.message in targets:
			if event.message==GAME["sheriff"]:
				respond(event,CANT_CHOOSE_SELF)
				return
			GAME["sheriff_chose"]=event.message
			if round_end(event):
				GAME["state"]=GameState.MAFIA
				PRIVMSG(CHANNEL,MAFIA_PUB)
				PRIVMSG(GAME["mafia"],MAFIA_PRIV)
				targets = [GAME[x] for x in "mafia doctor sheriff".split()]+GAME["townspeople"]
				if GAME["doctor_dead"]: targets.remove(GAME["doctor"])
				random.shuffle(targets)
				PRIVMSG(CHANNEL,LIST_TARGETS.format(",".format(targets)))
			else:
				GAME["state"]=GameState.NO_GAME
				GAME["mafia"]=None
				GAME["doctor"]=None
				GAME["sheriff"]=None
				GAME["townspeople"]=[]
				GAME["doctor_dead"]=False
		else:
			respond(event,INVALID_TARGET)
			respond(event,LIST_TARGETS.format(", ".join(targets)))
	else:
		respond(event,"It's not your turn to message the bot!")

def round_end(event):
	global GAME,CHANNEL
	sheriff_dead = False
	mafia_dead = False
	mafia_target = GAME["mafia_chose"]
	if mafia_target==GAME["sheriff"]:
		mafia_target=WAS_THE_SHERIFF.format(mafia_target)
	elif mafia_target==GAME["doctor"]:
		mafia_target=WAS_THE_DOCTOR.format(mafia_target)
	result = TARGET_DIED
	if GAME["mafia_chose"]==GAME["doctor_chose"]:
		result = TARGET_SAVED
	# only reveal role if player died
	PRIVMSG(CHANNEL,END_MSG_1.format(mafia_target if result==TARGET_DIED else GAME["mafia_chose"],result))
	if result==TARGET_DIED:
		if GAME["mafia_chose"]==GAME["doctor"]:
			GAME["doctor_dead"]=True
		elif GAME["mafia_chose"]==GAME["sheriff"]:
			sheriff_dead = True
		else:
			GAME["townspeople"].remove(GAME["mafia_chose"])
		if GAME["mafia_chose"]==GAME["sheriff_chose"]:
			PRIVMSG(CHANNEL,END_MSG_2C.format(GAME["mafia_chose"]))
			return True
	sheriff_target = GAME["sheriff_chose"]
	if sheriff_target == GAME["doctor"]:
		sheriff_target = WAS_THE_DOCTOR.format(sheriff_target)
	if not sheriff_dead:
		msg = END_MSG_2A.format(sheriff_target)
		correct = TARGET_CORRECT
		incorrect = TARGET_INCORRECT
	else:
		msg = END_MSG_2B.format(sheriff_target)+" {}"
		correct = END_2B_CORRECT
		incorrect = END_2B_INCORRECT
	if GAME["sheriff_chose"]==GAME["mafia"]:
		msg = msg.format(correct)
		PRIVMSG(CHANNEL,msg)
		mafia_dead=True
	else:
		msg = msg.format(incorrect)
		PRIVMSG(CHANNEL,msg)
	if mafia_dead or sheriff_dead:
		PRIVMSG(CHANNEL,ROUND_OVER)
		return False
	else:
		return True

def on_admin_debug(event):
	respond(event,repr(GAME))

def register(bot):
	global BOT
	BOT=bot
	bot.event_manager.on("privmsg",on_privmsg)
	bot.event_manager.on("command_join",on_command_join)
	bot.event_manager.on("command_start",on_command_start)
	bot.event_manager.on("admin_debug",on_admin_debug)
