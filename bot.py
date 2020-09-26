import impmod, socket, traceback, events, time, os
from irc.client import NickMask
class Socket:
	def __init__(self,server):
		self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		self.sock.connect(server)
		self._read_buffer=b""
	def read(self):
		try:
			data=self.sock.recv(4096)
			if not data:
				return None
		except: return traceback.print_exc()
		data = self._read_buffer+data
		self._read_buffer=b""
		lines = [line.strip(b"\r") for line in data.split(b"\n")]
		if lines[-1]:
			self._read_buffer=lines[-1]
		lines.pop(-1)
		lines = [line.decode("utf-8") for line in lines]
		return lines
	def send(self,line):
		self.sock.send(line.encode("utf-8"))
	def close(self):
		self.sock.shutdown(socket.SHUT_RDWR)
		self.sock.close()

def unescape(value):
	return value.replace(r"\:",";").replace(r"\s"," ").replace(r"\\","\\").replace(r"\r","\r").replace(r"\n","\n")

def escape(value):
	return value.replace(";",r"\:").replace(" ",r"\s").replace("\\",r"\\").replace("\r",r"\r").replace("\n",r"\n")

MISSING = None

class IRCLine:
	def __init__(self,command,*params,tags=dict(),hostmask=""):
		self.command=command
		if len(params)==0:
			self.params=[]
		elif len(params)==1 and type(params[0]) in (list,tuple):
			self.params=list(params[0])
		else:
			self.params=list(params)
		self.tags=tags
		self.hostmask=NickMask(hostmask) if hostmask else None
	@property
	def line(self):
		prefix=""
		if len(list(self.tags.keys()))>0:
			tagc = len(list(self.tags.keys()))
			prefix+="@"
			for i,tag in enumerate(self.tags.keys()):
				prefix+=tag
				if self.tags[tag] is not MISSING:
					prefix+="="+escape(str(self.tags[tag]))
				if (i+1)<tagc:
					prefix+=";"
			prefix+=" "
		if self.hostmask:
			prefix+=":{} ".format(self.hostmask)
		return prefix+" ".join([self.command]+self.params)+"\r\n"
	@classmethod
	def parse_line(cls,line):
		parts = line.split()
		tags = dict()
		if parts[0].startswith("@"):
			taglist = parts.pop(0)[1:].split(";")
			for tag in taglist:
				if "=" in tag:
					key, value = tag.split("=",1)
					tags[key]=unescape(value)
				else:
					tags[tag]=MISSING
		hostmask=None
		if parts[0].startswith(":"):
			hostmask=parts.pop(0)[1:]
		i=len(parts)-1
		while i>0 and not parts[i].startswith(":"): i-=1
		if i!=0: parts[i:]=[" ".join(parts[i:])]
		return cls(*parts,tags=tags,hostmask=hostmask)
	def encode(self,*args,**kwargs):
		# clearly, if we're here, I'm an idiot and am trying to send an
		# IRCLine object down the tube. just do it.
		return self.line.encode(*args,**kwargs)

PLUGIN_MODULES={}
class IRCBot:
	def __init__(self,nickname,username,realname="IRCBot",server=("localhost",6667),channels=["#bots"]):
		self.nickname=nickname
		self.username=username
		self.realname=realname
		self.server=server
		self.channels=channels
		self.event_manager=events.EventManager()
		self.in_batch=False
	def load_modules(self):
		self.event_manager.clear()
		for name in os.listdir("plugins"):
			if name.endswith(".py"):
				self.load_module(name[:-3],os.path.join("plugins",name))
	def load_module(self,modname,path):
		try:
			if modname in PLUGIN_MODULES:
				print("{} already imported, reloading".format(modname))
				teardown = getattr(PLUGIN_MODULES[modname].module,"teardown",None)
				if teardown: teardown()
				PLUGIN_MODULES[modname].reload()
			else:
				try:
					print("importing {}".format(modname))
					PLUGIN_MODULES[modname]=impmod.Module(modname,path)
				except:
					print("Unable to load plugin {}".format(modname))
					traceback.print_exc()
			register_func = getattr(PLUGIN_MODULES[modname].module,"register",None)
			if not register_func:
				print(f"Plugin {modname} has no register function!")
				print("Remember, if porting plugins from a minerbot-based architecture,")
				print("you have to add a register function to use the new system.")
				return
			register_func(self)
		except:
			traceback.print_exc()
			pass
	def handle_line(self,line):
		if type(line)!=IRCLine: line = IRCLine.parse_line(line)
		self.event_manager(events.Event("raw_line",text=line.line,parsed=line))
		if line.command=="PING":
			line.command="PONG"
			self.socket.send(line.line)
			return
		if line.command=="BATCH":
			self.in_batch = line.params[0].startswith("+")
		if line.hostmask is None: return
		if line.hostmask.nick==self.nickname:
			return
		if line.command in "PRIVMSG NOTICE".split():
			target = line.params[0]
			message = line.params[1][1:]
			self.event_manager(events.Event(line.command.lower(),target=target,message=message,tags=line.tags,hostmask=line.hostmask))
		elif line.command == "TAGMSG":
			self.event_manager(events.Event("tagmsg",hostmask=line.hostmask,tags=line.tags,target=line.params[0]))
		elif line.command == "INVITE":
			self.event_manager(events.Event("invite",to=line.params[1][1:],hostmask=line.hostmask))
		elif line.command == "PING":
			self.socket.send(IRCLine("PONG",line.params).line)
	def start(self):
		self.socket = Socket(self.server)
		self.socket.send("NICK {}\r\n".format(self.nickname))
		self.socket.send("USER {} * * :{}\r\n".format(self.username,self.realname))
		time.sleep(2) # give the server some time to record my username
		self.event_manager(events.Event("connection_established"))
		for channel in self.channels:
			self.socket.send(f"JOIN {channel}\r\n")
			time.sleep(1)
		self.socket.send("CAP REQ account-tag\r\n")
		self.running=True
		while self.running:
			lines = self.socket.read()
			if lines:
				for line in lines:
					self.handle_line(line)
		self.socket.close()
		del self.socket

if __name__=="__main__":
	bot = IRCBot("mafiabot","mafiabot",channels=["#mafia"])
	bot.load_modules()
	bot.start()
