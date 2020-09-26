import plugin
class DictData(plugin.JSONData):
	def __init__(self,filename,**kwargs):
		plugin.JSONData.__init__(self,kwargs)
		self.filename = filename
		self.load(self.filename)
	def __getitem__(self,k):
		self.load(self.filename)
		return self.value[k]
	def __setitem__(self,k,v):
		self.value[k]=v
		self.save(self.filename)
	def __contains__(self,k):
		return k in self.value
	def get(self,k,default=None):
		self.load(self.filename)
		return self.value.get(k,default)
