from bot import IRCLine
from events import Event
BOT = None

def on_botlist(event):
	if not BOT: return None
	commands = []
	for handler in BOT.event_manager.handlers.keys():
		if handler.startswith("command_"):
			command = handler[len("command_"):]
			if command not in "admin botlist".split(): commands.append(command)
	print(commands)
	BOT.socket.send(IRCLine("PRIVMSG",event.target,":{}: I'm minerbot2, rewritten again! Commands include {}".format(event.hostmask.nick,", ".join(["!"+x for x in commands]))))

def on_privmsg(event):
	if BOT.in_batch: return
	if BOT and BOT.prefix=="!": return
	if event.message in ("!botlist", "!rollcall"):
		ev = Event("command_botlist",parts=[])
		ev.data.update(event.data)
		on_botlist(ev)

def register(bot):
	global BOT
	BOT=bot
	bot.event_manager.on("command_botlist",on_botlist)
	bot.event_manager.on("privmsg",on_privmsg)
