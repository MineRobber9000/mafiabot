from bot import IRCLine
BOT = None

def on_admin_raw(event):
	# normalize and send line
	BOT.socket.send(IRCLine.parse_line(" ".join(event.parts)).line)

def on_admin_action(event):
	target = event.parts[0]
	message = " ".join(event.parts[1:])
	BOT.socket.send(IRCLine("PRIVMSG",target,f":\x01ACTION {message}\x01"))

def register(bot):
	global BOT
	BOT=bot
	bot.event_manager.on("admin_raw",on_admin_raw)
	bot.event_manager.on("admin_action",on_admin_action)
