import importlib, events
importlib.reload(events)
from events import Event
from bot import IRCLine
ADMIN_HOSTMASKS = [x+"!khuxkm@sudoers.tilde.team" for x in "khuxkm khuxkm|lounge".split()]
BOT = None

def admin(event):
	if BOT is None: return
	if event.hostmask not in ADMIN_HOSTMASKS:
		BOT.socket.send(IRCLine("PRIVMSG","#meta","You're not the boss of me! (hostmask {!s})".format(event.hostmask)).line)
		return
	if len(event.parts)==0: return
	if event.parts[0]=="reload":
		BOT.load_modules()
	elif event.parts[0]=="quit":
		BOT.socket.send(IRCLine("QUIT",[":goodbye"]).line)
		BOT.running=False
	elif event.parts[0]=="msg":
		target = event.parts[1]
		message = ":"+" ".join(event.parts[2:])
		BOT.socket.send(IRCLine("PRIVMSG",target,message).line)
	else:
		event_out = Event("admin_"+event.parts[0])
		event_out.data.update(event.data)
		event_out.data["parts"]=event.parts[1:]
		BOT.event_manager(event_out)

def on_invite(event):
	if BOT is None: return
	if event.hostmask not in ADMIN_HOSTMASKS: return
	BOT.socket.send(IRCLine("JOIN",[event.to]).line)

PASSWORD="whoops"
try:
	with open(".password") as f: PASSWORD=f.read().strip()
except: pass
def login(event):
	BOT.socket.send(IRCLine("CAP","REQ","batch").line)
	BOT.socket.send(IRCLine("NS","IDENTIFY",PASSWORD).line)

def register(bot):
	global BOT
	BOT=bot
	bot.event_manager.on("command_admin",admin)
	bot.event_manager.on("invite",on_invite)
	bot.event_manager.on("connection_established",login)
