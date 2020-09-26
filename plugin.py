import json, traceback
help = {}
class CommandGroup:
	def __init__(self,f,default="help"):
		self.base = f
		self.subcmds = {}
		self.subcmds_help = {}
		self.default = default
	def command(self,name,help=""):
		self.subcmds_help[name]=help
		def _register_subcmd(f):
			self.subcmds[name]=f
			return f
		return _register_subcmd
	def __call__(self,bot,channel,nick,subcmd="",*args):
		print("Calling base")
		if self.base(bot,channel,nick,subcmd,*args):
			return
		print("Calling subcommand {}".format(subcmd if subcmd in self.subcmds else self.default))
		if subcmd in self.subcmds:
			return self.subcmds[subcmd](bot,channel,nick,subcmd,*args)
		else:
#			return self.subcmds[self.default](bot,channel,nick,subcmd,*args)
			return

class Data:
	"""A class for plugin data."""
	def __init__(self,value):
		self.value = value
	def serialize(self):
		return self.value
	def deserialize(self,value):
		self.value = value
	def save(self,filename):
		with open(filename,"w") as f:
			f.write(self.serialize())
	def load(self,filename):
		try:
			with open(filename) as f:
				self.deserialize(f.read())
		except:
			print("Error loading data from {!r}:".format(filename))
			traceback.print_exc()
			pass # You should've initialized this with a sane default, so just keep the default on error

class JSONData(Data):
	"""Data, but can be serialized to JSON (and should be)."""
	def serialize(self):
		return json.dumps(self.value)
	def deserialize(self,value):
		self.value = json.loads(value)

def clear():
	cmds.clear()
	help.clear()
	listeners.clear()

#def command(name,helptext="No help available for this command."):
#	def _register_cmd(func):
#		cmds[name]=func
#		help[name]=helptext
#		return func
#	return _register_cmd

def group(name,helptext=""):
	def _register_group(f):
		gr = CommandGroup(f)
		return gr
	return _register_group

def listener(name):
	def _register_cmd(func):
		listeners[name]=func
		return func
	return _register_cmd

def alias(name,target):
	cmds[name]=cmds[target]
	help[name]=help[target]
