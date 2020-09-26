import importlib, importlib.util, sys

class Module:
	"""A module. Stores module object, spec object, and handles reloading."""
	def __init__(self,modname,path=None):
		if path is None:
			path = modname+".py"
		self.modname, self.path = modname, path
		self.spec = importlib.util.spec_from_file_location(modname,path)
		self.module = importlib.util.module_from_spec(self.spec)
		self.spec.loader.exec_module(self.module)
	def reload(self):
		if self.modname not in sys.modules:
			sys.modules[self.modname]=self.module
		# Alright, this needs some explaining.
		# When you do importlib.reload, it does some juju magic shist to find the spec and calls importlib._bootstrap._exec.
		# When you dynamically import a module it won't do its magic correctly and it'll error.
		# Luckily, we can skip all the juju magic since we can just store the spec.
		importlib._bootstrap._exec(self.spec,self.module)
