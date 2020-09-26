import events
BOT=None

def on_privmsg(event):
	if BOT is None: return
	if BOT.in_batch: return
	prefix = BOT.prefix if event.target.startswith("#") else ""
	if event.message.startswith(prefix):
		parts = event.message.split(" ")
		parts[0]=parts[0][len(prefix):]
		event_out = events.Event("command_"+parts.pop(0),parts=parts)
		event_out.data.update(event.data)
		BOT.event_manager(event_out)

def register(bot):
	global BOT
	BOT=bot
	bot.prefix="!"
	bot.event_manager.on("privmsg",on_privmsg)
