import traceback, sys
from bot import IRCLine
BOT = None

def on_admin_eval(event):
	global BOT
	text = " ".join(event.parts)
	try:
		ret = exec(text,globals(),locals())
	except:
		ret = traceback.format_exception_only(*sys.exc_info()[:2])[-1]
	BOT.socket.send(IRCLine("PRIVMSG",event.target if event.target.startswith("#") else event.hostmask.nick,":"+(repr(ret) if type(ret)!=str else ret)))

def register(bot):
	global BOT
	BOT=bot
	bot.event_manager.on("admin_eval",on_admin_eval)
